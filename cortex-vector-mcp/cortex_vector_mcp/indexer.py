"""Cold-start indexer: parse `docs/adr/ADR-*.md` into the vector store.

The ADRs in this repo are hand-written markdown, so the parser is deliberately
forgiving about field order and heading wording. What it will *not* do is invent
a value: a file missing an author or a date is reported as a skip with a reason,
never silently indexed with a placeholder, because a wrong author means paging
the wrong human.

Usage:
    python -m cortex_vector_mcp.indexer [--adr-dir docs/adr] [--dry-run]
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

from .schema import ADRValidationError, validate_adr
from .store import Store

log = logging.getLogger(__name__)

# `**Status:** ACTIVE` / `**Author:** @senior-dev` / `**Merged in PR:** #89`
FIELD_RE = re.compile(r"^\*\*(?P<key>[^:*]+):\*\*\s*(?P<value>.*?)\s*$", re.MULTILINE)
# `# ADR-002: Redis for Distributed Session Persistence`
TITLE_RE = re.compile(r"^#\s*(?P<id>ADR-\d{3,})\s*[:\-]\s*(?P<title>.+?)\s*$", re.MULTILINE)
ID_FROM_NAME_RE = re.compile(r"(ADR-\d{3,})", re.IGNORECASE)

FIELD_ALIASES = {
    "status": "status",
    "date": "date",
    "author": "author",
    "authors": "author",
    "merged in pr": "merged_pr",
    "merged pr": "merged_pr",
    "pr": "merged_pr",
    "superseded by": "superseded_by_adr",
    "superseded by adr": "superseded_by_adr",
    "supersedes": "supersedes",
}

SECTION_ALIASES = {
    "rationale": "reasoning",
    "reasoning": "reasoning",
    "context": "context",
    "decision": "decision",
    "invariant": "invariants",
    "invariants": "invariants",
    "alternatives": "alternatives",
    "alternatives rejected": "alternatives",
    "alternatives considered": "alternatives",
    "scope": "scope_files",
    "affected files": "scope_files",
    "affected files / modules": "scope_files",
}


def _split_sections(body: str) -> dict[str, str]:
    """Map `## Heading` -> raw text beneath it (lowercased heading keys)."""
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^##+\s*(.+?)\s*$", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip().lower()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def _bullets(text: str) -> list[str]:
    """Pull `- ` / `1. ` bullets, else fall back to non-empty lines."""
    items = [
        re.sub(r"^\s*(?:[-*]|\d+\.)\s*", "", ln).strip()
        for ln in text.splitlines()
        if re.match(r"^\s*(?:[-*]|\d+\.)\s+", ln)
    ]
    if items:
        # Strip leading bold labels like `**Rule:** ...` for readability.
        return [re.sub(r"^\*\*[^*]+:\*\*\s*", "", i).strip() for i in items if i]
    stripped = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return stripped


def _extract_paths(*texts: str) -> list[str]:
    """Find file-ish tokens (`src/cache/session.py`, `/src/core/`) in prose."""
    found: list[str] = []
    for text in texts:
        for m in re.finditer(r"`([^`\n]+)`", text):
            token = m.group(1).strip()
            if "/" in token and " " not in token:
                found.append(token)
    seen: set[str] = set()
    return [p for p in found if not (p in seen or seen.add(p))]


def parse_adr_markdown(path: Path) -> dict[str, Any]:
    """Parse one ADR markdown file into an unvalidated payload dict."""
    text = path.read_text(encoding="utf-8")

    payload: dict[str, Any] = {"source_path": str(path)}

    title_match = TITLE_RE.search(text)
    if title_match:
        payload["id"] = title_match.group("id").upper()
        payload["title"] = title_match.group("title").strip()
    else:
        # Fall back to the filename: ADR-002-distributed-cache-redis.md
        name_match = ID_FROM_NAME_RE.search(path.name)
        if name_match:
            payload["id"] = name_match.group(1).upper()
        heading = re.search(r"^#\s*(.+?)\s*$", text, re.MULTILINE)
        if heading:
            payload["title"] = heading.group(1).strip()

    for m in FIELD_RE.finditer(text):
        key = m.group("key").strip().lower()
        value = m.group("value").strip()
        mapped = FIELD_ALIASES.get(key)
        if mapped and value:
            payload[mapped] = value

    sections = _split_sections(text)
    reasoning_parts: list[str] = []
    for heading, content in sections.items():
        mapped = SECTION_ALIASES.get(heading)
        if mapped == "invariants":
            payload["invariants"] = _bullets(content)
        elif mapped == "alternatives":
            payload["alternatives"] = _bullets(content)
        elif mapped == "scope_files":
            payload["scope_files"] = _extract_paths(content) or _bullets(content)
        elif mapped in ("reasoning", "context", "decision"):
            reasoning_parts.append(content)

    if reasoning_parts:
        payload["reasoning"] = "\n\n".join(p for p in reasoning_parts if p).strip()

    # Scope is what makes path-based retrieval work, so if the ADR never spells
    # it out, harvest any code paths mentioned anywhere in the document.
    if not payload.get("scope_files"):
        harvested = _extract_paths(text)
        if harvested:
            payload["scope_files"] = harvested

    return payload


def index_directory(
    adr_dir: Path, store: Store, dry_run: bool = False
) -> tuple[list[str], list[tuple[str, str]]]:
    """Index every `ADR-*.md` under `adr_dir`.

    Returns:
        (indexed_ids, [(filename, reason_skipped), ...])
    """
    files = sorted(adr_dir.glob("ADR-*.md"))
    indexed: list[str] = []
    skipped: list[tuple[str, str]] = []

    for path in files:
        try:
            payload = parse_adr_markdown(path)
        except Exception as exc:  # noqa: BLE001 - report, never abort the batch
            skipped.append((path.name, f"parse error: {exc}"))
            continue
        try:
            if dry_run:
                validate_adr(payload)
            else:
                store.upsert_decision(payload)
            indexed.append(payload.get("id", path.stem))
        except ADRValidationError as exc:
            skipped.append((path.name, str(exc)))

    return indexed, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index ADR markdown into cortex vector memory.")
    parser.add_argument("--adr-dir", default="docs/adr", help="directory of ADR-*.md files")
    parser.add_argument("--persist-dir", default=None, help="ChromaDB persist directory")
    parser.add_argument("--dry-run", action="store_true", help="parse and validate without writing")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    adr_dir = Path(args.adr_dir)
    if not adr_dir.is_dir():
        print(f"error: {adr_dir} is not a directory", file=sys.stderr)
        return 2

    store = Store(args.persist_dir)
    print(f"backend: {store.backend} ({'semantic' if store.semantic else 'lexical fallback'})")

    indexed, skipped = index_directory(adr_dir, store, dry_run=args.dry_run)

    verb = "would index" if args.dry_run else "indexed"
    print(f"{verb} {len(indexed)}: {', '.join(indexed) or '(none)'}")
    if skipped:
        print(f"skipped {len(skipped)}:")
        for name, reason in skipped:
            print(f"  - {name}: {reason}")
    if not args.dry_run:
        print(f"total ADRs in store: {store.count()}")

    # A run that indexed nothing at all is a failure worth a non-zero exit.
    return 0 if indexed else 1


if __name__ == "__main__":
    raise SystemExit(main())
