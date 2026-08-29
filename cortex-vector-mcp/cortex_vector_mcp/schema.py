"""ADR schema definition and validation.

The vector store is the single source of truth the agent reasons over, so a
malformed record is worse than a missing one: it produces confident, wrong
escalations. Everything entering the store passes through `validate_adr`.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date as _date
from typing import Any

# ADR-001 lives at docs/ADR-001-codebase-cortex.md (project charter); the
# numbered architectural records live under docs/adr/.
ADR_ID_RE = re.compile(r"^ADR-\d{3,}$")

VALID_STATUSES = ("ACTIVE", "SUPERSEDED", "DEPRECATED", "PROPOSED")

#: Metadata keys whose values are lists. Chroma metadata only accepts scalars,
#: so these are JSON-encoded on write and decoded on read.
LIST_FIELDS = ("scope_files", "invariants", "alternatives")


class ADRValidationError(ValueError):
    """Raised when an ADR payload cannot be stored as-is."""


@dataclass
class ADR:
    """A validated architectural decision record."""

    id: str
    title: str
    author: str
    date: str
    status: str = "ACTIVE"
    reasoning: str = ""
    scope_files: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    merged_pr: int | None = None
    superseded_by_adr: str | None = None
    superseded_by_pr: int | None = None
    source_path: str | None = None

    # -- embedding & storage -------------------------------------------------

    def embedding_text(self) -> str:
        """The text actually embedded.

        Retrieval must match on *concepts and file scope*, not prose style, so
        the invariants and scope paths are woven in rather than left as
        metadata. A diff touching `src/cache/session.py` should retrieve an ADR
        whose scope names that path even when the wording shares no vocabulary.
        """
        parts = [
            self.title,
            f"Status: {self.status}",
            self.reasoning,
        ]
        if self.invariants:
            parts.append("Invariants: " + " ".join(self.invariants))
        if self.alternatives:
            parts.append("Alternatives rejected: " + " ".join(self.alternatives))
        if self.scope_files:
            parts.append("Applies to: " + " ".join(self.scope_files))
        return "\n".join(p for p in parts if p)

    def to_metadata(self) -> dict[str, Any]:
        """Flatten to Chroma-safe scalar metadata."""
        meta: dict[str, Any] = {}
        for key, value in asdict(self).items():
            if key in LIST_FIELDS:
                meta[key] = json.dumps(value or [])
            elif value is None:
                # Chroma rejects None; omit the key entirely instead.
                continue
            else:
                meta[key] = value
        return meta

    @classmethod
    def from_metadata(cls, meta: dict[str, Any]) -> "ADR":
        """Inverse of `to_metadata`."""
        data = dict(meta)
        for key in LIST_FIELDS:
            raw = data.get(key)
            if isinstance(raw, str):
                try:
                    data[key] = json.loads(raw)
                except json.JSONDecodeError:
                    data[key] = []
            elif raw is None:
                data[key] = []
        known = {f for f in cls.__dataclass_fields__}  # noqa: SLF001
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        # Accept a single string or a comma/newline separated list.
        parts = [p.strip() for p in re.split(r"[\n,]", value)]
        return [p for p in parts if p]
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    raise ADRValidationError(f"{field_name} must be a string or list, got {type(value).__name__}")


def _as_optional_int(value: Any, field_name: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ADRValidationError(f"{field_name} must be an integer, got bool")
    try:
        return int(str(value).lstrip("#"))
    except (TypeError, ValueError) as exc:
        raise ADRValidationError(f"{field_name} must be an integer, got {value!r}") from exc


def validate_adr(payload: dict[str, Any]) -> ADR:
    """Validate and normalise an ADR payload.

    Raises:
        ADRValidationError: with a message naming every problem found, so a
            caller fixing a record does not have to fix it one field per round
            trip.
    """
    if not isinstance(payload, dict):
        raise ADRValidationError(f"ADR payload must be an object, got {type(payload).__name__}")

    problems: list[str] = []

    adr_id = str(payload.get("id", "")).strip().upper()
    if not adr_id:
        problems.append("id is required")
    elif not ADR_ID_RE.match(adr_id):
        problems.append(f"id must look like ADR-002, got {adr_id!r}")

    title = str(payload.get("title", "")).strip()
    if not title:
        problems.append("title is required")

    # Author is how escalation finds a human, so an empty one is a real defect.
    author = str(payload.get("author", "")).strip().lstrip("@")
    if not author:
        problems.append("author is required (it is who gets paged)")

    status = str(payload.get("status", "ACTIVE")).strip().upper()
    if status not in VALID_STATUSES:
        problems.append(f"status must be one of {', '.join(VALID_STATUSES)}, got {status!r}")

    raw_date = str(payload.get("date", "")).strip()
    if not raw_date:
        raw_date = _date.today().isoformat()
    else:
        # Accept YYYY-MM-DD, tolerate a full ISO timestamp.
        candidate = raw_date[:10]
        try:
            _date.fromisoformat(candidate)
            raw_date = candidate
        except ValueError:
            problems.append(f"date must be ISO YYYY-MM-DD, got {raw_date!r}")

    try:
        scope_files = _as_list(payload.get("scope_files") or payload.get("affected_paths"), "scope_files")
        invariants = _as_list(payload.get("invariants"), "invariants")
        alternatives = _as_list(payload.get("alternatives"), "alternatives")
    except ADRValidationError as exc:
        problems.append(str(exc))
        scope_files = invariants = alternatives = []

    try:
        merged_pr = _as_optional_int(payload.get("merged_pr"), "merged_pr")
        superseded_by_pr = _as_optional_int(payload.get("superseded_by_pr"), "superseded_by_pr")
    except ADRValidationError as exc:
        problems.append(str(exc))
        merged_pr = superseded_by_pr = None

    superseded_by_adr = payload.get("superseded_by_adr")
    if superseded_by_adr:
        superseded_by_adr = str(superseded_by_adr).strip().upper()
        if not ADR_ID_RE.match(superseded_by_adr):
            problems.append(f"superseded_by_adr must look like ADR-004, got {superseded_by_adr!r}")
    else:
        superseded_by_adr = None

    # A SUPERSEDED record with no pointer to its replacement is a dead end for
    # lineage tracing, which is the whole point of cortex-explain.
    if status == "SUPERSEDED" and not superseded_by_adr:
        problems.append("status SUPERSEDED requires superseded_by_adr")

    reasoning = str(payload.get("reasoning") or "").strip()
    if not reasoning and not invariants:
        problems.append("an ADR needs at least one of reasoning or invariants to be useful")

    if problems:
        raise ADRValidationError("; ".join(problems))

    return ADR(
        id=adr_id,
        title=title,
        author=author,
        date=raw_date,
        status=status,
        reasoning=reasoning,
        scope_files=scope_files,
        invariants=invariants,
        alternatives=alternatives,
        merged_pr=merged_pr,
        superseded_by_adr=superseded_by_adr,
        superseded_by_pr=superseded_by_pr,
        source_path=(str(payload["source_path"]) if payload.get("source_path") else None),
    )
