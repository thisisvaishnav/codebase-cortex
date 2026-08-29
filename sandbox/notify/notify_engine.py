#!/usr/bin/env python3
"""cortex-notify engine helper: CODEOWNERS resolution, mention hygiene, comment formatting, and hash dedup.

Standard library only (runs inside sandbox or CLI).
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import sys


def parse_codeowners_rules(content: str) -> list[tuple[str, list[str]]]:
    """Parse CODEOWNERS file into a list of (pattern, owners) tuples."""
    rules = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            pattern = parts[0]
            owners = parts[1:]
            rules.append((pattern, owners))
    return rules


def match_path(path: str, pattern: str) -> bool:
    """Determine if a relative path matches a CODEOWNERS pattern according to GitHub rules."""
    path = path.lstrip("/")
    pat = pattern

    anchored = pat.startswith("/")
    if anchored:
        pat = pat[1:]

    is_dir_only = pat.endswith("/")
    if is_dir_only:
        pat = pat[:-1]

    if pat == "*" or pat == "**":
        return True

    # If pattern contains no slash and is not anchored, match anywhere in path segments
    if "/" not in pat and not anchored:
        segments = path.split("/")
        if is_dir_only:
            return pat in segments[:-1]
        return any(fnmatch.fnmatchcase(seg, pat) for seg in segments)

    # Prefix / Glob matching
    if is_dir_only:
        return path == pat or path.startswith(pat + "/")

    if fnmatch.fnmatchcase(path, pat) or fnmatch.fnmatchcase(path, pat + "/*"):
        return True

    if path == pat or path.startswith(pat + "/"):
        return True

    return False


def resolve_codeowners(content: str, affected_paths: list[str]) -> list[str]:
    """Resolve responsible code owners for affected file paths based on GitHub matching rules.
    
    Rule: Last matching rule wins per file. Union across all affected files.
    """
    rules = parse_codeowners_rules(content)
    winning_owners = set()

    for path in affected_paths:
        path_winner = None
        for pattern, owners in rules:
            if match_path(path, pattern):
                path_winner = owners
        if path_winner:
            for owner in path_winner:
                winning_owners.add(owner)

    return sorted(list(winning_owners))


def clean_handle(handle: str) -> str:
    """Normalise handle to lowercase without leading @."""
    return handle.lstrip("@").strip().lower()


def resolve_mentions(
    original_author: str | None,
    codeowners: list[str],
    pr_author: str | None,
    confidence: float,
) -> list[str]:
    """Resolve mentions list applying confidence threshold and self-tag hygiene."""
    if confidence < 0.80:
        return []

    pr_author_clean = clean_handle(pr_author) if pr_author else ""
    mentions = []

    if original_author:
        author_handle = "@" + clean_handle(original_author)
        if clean_handle(original_author) != pr_author_clean:
            mentions.append(author_handle)

    for owner in codeowners:
        owner_handle = "@" + clean_handle(owner)
        if clean_handle(owner) != pr_author_clean and owner_handle not in mentions:
            mentions.append(owner_handle)

    return mentions


def normalize_markdown(body: str) -> str:
    """Normalise markdown body for sha256 content hashing."""
    # Strip cortex comment markers
    text = re.sub(r"<!--\s*codebase-cortex:pr-analysis\s*-->", "", body)
    text = re.sub(r"<!--\s*cortex:hash:[a-f0-9]+\s*-->", "", body)
    # Strip dynamic timestamps / relative times
    text = re.sub(r"·\s*[\w\s]+\s*ago", "", text)
    text = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?", "", text)
    return text.strip()


def compute_content_hash(body: str) -> str:
    """Compute 12-character hex sha256 hash of normalized comment body."""
    normalized = normalize_markdown(body)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def format_comment(
    verdict: dict,
    pr_author: str | None = None,
    codeowners_content: str = "",
    standing_comment: str | None = None,
) -> dict:
    """Format single-upsert comment with dedup hash and escalation logic."""
    confidence = float(verdict.get("confidence", 0.0))
    classification = verdict.get("classification", "COMPLIANT")
    has_violation = verdict.get("has_violation", False)
    affected_files = verdict.get("affected_files", [])
    original_author = verdict.get("author")

    resolved_owners = resolve_codeowners(codeowners_content, affected_files) if codeowners_content else []
    mentions = resolve_mentions(original_author, resolved_owners, pr_author, confidence)

    # 1. Violation Escalation Comment (confidence >= 0.80)
    if has_violation and confidence >= 0.80:
        adr_id = verdict.get("violated_adr_id", "ADR-???")
        adr_title = verdict.get("violated_adr_title", "Architectural Decision")
        adr_file = f"{adr_id.lower()}.md"
        reason = verdict.get("reason", "Violates architectural invariant.")
        
        files_str = ", ".join(f"`{f}`" for f in affected_files) if affected_files else "`repository files`"
        author_display = original_author or "maintainer"
        
        esc_line = ""
        if mentions:
            esc_line = f"🔔 **Maintainer Escalation:** Paging {', '.join(mentions)} for architectural review."
        elif pr_author and clean_handle(pr_author) == clean_handle(author_display):
            esc_line = f"ℹ️ **Maintainer Note:** PR author (@{clean_handle(pr_author)}) is the original decision author and path owner."
        else:
            esc_line = "🔔 **Maintainer Escalation:** Paging code owners for architectural review."

        body = (
            "<!-- codebase-cortex:pr-analysis -->\n"
            "⚠️ **Codebase Cortex — Architectural Conflict Detected**\n\n"
            "This change appears to contradict a foundational architectural decision.\n\n"
            f"- **Violated Decision:** [{adr_id}: {adr_title}](docs/adr/{adr_file})\n"
            f"- **Original Reasoning (by {author_display}):** {reason}\n"
            f"- **Confidence Score:** {int(confidence * 100)}% ({classification})\n"
            f"- **Files Affected:** {files_str}\n\n"
            f"{esc_line}\n\n"
            "*If this change is intentional, please update the decision record in this PR's description and tick the architectural decision checkbox.*\n\n"
            "— *Powered by Codebase Cortex + TrueForge + Qodo*"
        )

    # 2. Advisory Comment (0.60 <= confidence < 0.80)
    elif classification == "ADVISORY" or (0.60 <= confidence < 0.80):
        adr_id = verdict.get("violated_adr_id", "ADR")
        adr_title = verdict.get("violated_adr_title", "Architectural Boundary")
        reason = verdict.get("reason", "Touches architectural boundary.")
        files_str = ", ".join(f"`{f}`" for f in affected_files) if affected_files else "`repository files`"

        body = (
            "<!-- codebase-cortex:pr-analysis -->\n"
            "💡 **Codebase Cortex — Architectural Advisory**\n\n"
            "This change touches an architectural boundary or pattern.\n\n"
            f"- **Related Decision:** {adr_id}: {adr_title}\n"
            f"- **Analysis:** {reason}\n"
            f"- **Confidence Score:** {int(confidence * 100)}% (ADVISORY)\n"
            f"- **Files Affected:** {files_str}\n\n"
            "No maintainer escalation required.\n\n"
            "— *Powered by Codebase Cortex + TrueForge + Qodo*"
        )

    # 3. Clean Audit Badge (< 0.60 or COMPLIANT)
    else:
        ratchet_note = ""
        if standing_comment and ("⚠️" in standing_comment or "Conflict Detected" in standing_comment):
            ratchet_note = "\n\n*(Previous architectural conflict has been resolved by developer updates.)*"

        body = (
            "<!-- codebase-cortex:pr-analysis -->\n"
            "✅ **Codebase Cortex — Architectural Audit Passed**\n\n"
            f"No architectural invariant conflicts detected against active ADRs.{ratchet_note}\n\n"
            "— *Powered by Codebase Cortex + TrueForge + Qodo*"
        )

    content_hash = compute_content_hash(body)
    full_body = f"{body}\n<!-- cortex:hash:{content_hash} -->"

    # Dedup & quiet window check against standing comment
    action = "create"
    if standing_comment:
        existing_hash_match = re.search(r"<!--\s*cortex:hash:([a-f0-9]+)\s*-->", standing_comment)
        existing_hash = existing_hash_match.group(1) if existing_hash_match else ""
        if existing_hash == content_hash:
            action = "skip"
        else:
            action = "update"

    return {
        "action": action,
        "body": full_body,
        "hash": content_hash,
        "mentions": mentions,
        "codeowners": resolved_owners,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: notify_engine.py <verdict.json> [pr_author] [codeowners_file]")
        sys.exit(1)

    verdict_path = sys.argv[1]
    pr_author = sys.argv[2] if len(sys.argv) > 2 else None
    codeowners_path = sys.argv[3] if len(sys.argv) > 3 else ".github/CODEOWNERS"

    with open(verdict_path, "r", encoding="utf-8") as f:
        verdict = json.load(f)

    codeowners_content = ""
    if os.path.exists(codeowners_path):
        with open(codeowners_path, "r", encoding="utf-8") as f:
            codeowners_content = f.read()

    res = format_comment(verdict, pr_author, codeowners_content)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
