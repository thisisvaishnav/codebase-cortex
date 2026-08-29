"""Vector store for ADRs, with a dependency-free fallback.

Two backends, same interface:

* **chroma** — ChromaDB with cosine space and its bundled MiniLM embeddings.
  Genuine dense semantic retrieval. Used when `chromadb` imports.
* **lexical** — a stdlib TF-IDF cosine index. No dependencies at all. Retrieval
  is *lexical, not semantic*: it matches shared vocabulary and path fragments,
  not paraphrase. Good enough for a handful of ADRs and it keeps the demo alive
  on a machine where chromadb will not install.

`Store.backend` reports which one is live, and every search result carries it,
so callers can be honest about retrieval quality instead of implying semantics
that the lexical path does not deliver.
"""

from __future__ import annotations

import logging
import math
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .schema import ADR, validate_adr

log = logging.getLogger(__name__)

ADR_COLLECTION = "adr_collection"
DIFF_COLLECTION = "diff_embeddings"

#: Cosine similarity floor for a candidate to be considered at all.
#: Calibrated in README.md; overridable per call.
DEFAULT_THRESHOLD = 0.70


# --------------------------------------------------------------------- lexical

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokens, plus path components split on separators.

    `src/cache/session.py` yields `src`, `cache`, `session`, `py` so a diff's
    file paths can match an ADR's declared scope.
    """
    lowered = text.lower()
    # Split camelCase and snake/path separators into word boundaries.
    lowered = re.sub(r"([a-z])([A-Z])", r"\1 \2", lowered)
    return _TOKEN_RE.findall(lowered)


class _LexicalIndex:
    """Minimal TF-IDF cosine index. Rebuilds on write; the corpus is tiny."""

    def __init__(self) -> None:
        self._docs: dict[str, list[str]] = {}
        self._meta: dict[str, dict[str, Any]] = {}
        self._idf: dict[str, float] = {}
        self._vectors: dict[str, dict[str, float]] = {}

    def upsert(self, doc_id: str, text: str, metadata: dict[str, Any]) -> None:
        self._docs[doc_id] = _tokenize(text)
        self._meta[doc_id] = metadata
        self._reindex()

    def delete(self, doc_id: str) -> None:
        self._docs.pop(doc_id, None)
        self._meta.pop(doc_id, None)
        self._vectors.pop(doc_id, None)
        self._reindex()

    def get(self, doc_id: str) -> dict[str, Any] | None:
        return self._meta.get(doc_id)

    def all_metadata(self) -> list[dict[str, Any]]:
        return list(self._meta.values())

    def _reindex(self) -> None:
        n = len(self._docs)
        if not n:
            self._idf, self._vectors = {}, {}
            return
        df: Counter[str] = Counter()
        for tokens in self._docs.values():
            df.update(set(tokens))
        # Smoothed IDF keeps a term present in every document from going to
        # exactly zero, which would erase short documents entirely.
        self._idf = {t: math.log((n + 1) / (c + 0.5)) + 1.0 for t, c in df.items()}
        self._vectors = {d: self._vectorize(toks) for d, toks in self._docs.items()}

    def _vectorize(self, tokens: Iterable[str]) -> dict[str, float]:
        tf = Counter(tokens)
        if not tf:
            return {}
        vec = {t: (c / len(tf)) * self._idf.get(t, 1.0) for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def query(self, text: str, limit: int) -> list[tuple[str, float, dict[str, Any]]]:
        qvec = self._vectorize(_tokenize(text))
        if not qvec:
            return []
        scored: list[tuple[str, float, dict[str, Any]]] = []
        for doc_id, dvec in self._vectors.items():
            # Cosine of two unit vectors is their dot product.
            shared = qvec.keys() & dvec.keys()
            sim = sum(qvec[t] * dvec[t] for t in shared)
            if sim > 0:
                scored.append((doc_id, sim, self._meta[doc_id]))
        scored.sort(key=lambda r: r[1], reverse=True)
        return scored[:limit]


# ----------------------------------------------------------------------- store


class Store:
    """ADR vector memory."""

    def __init__(self, persist_dir: str | os.PathLike[str] | None = None) -> None:
        self.persist_dir = Path(
            persist_dir or os.environ.get("CORTEX_CHROMA_DIR", "./chromadb_data")
        ).expanduser()
        self.backend = "lexical"
        self._client = None
        self._adrs = None
        self._diffs = None
        self._lex_adrs = _LexicalIndex()
        self._lex_diffs = _LexicalIndex()
        self._try_chroma()

    # -- backend selection ---------------------------------------------------

    def _try_chroma(self) -> None:
        if os.environ.get("CORTEX_FORCE_LEXICAL") == "1":
            log.warning("CORTEX_FORCE_LEXICAL=1 - using the lexical fallback backend")
            return
        try:
            import chromadb  # noqa: PLC0415
        except Exception as exc:  # pragma: no cover - depends on the machine
            log.warning(
                "chromadb unavailable (%s) - falling back to the stdlib lexical index. "
                "Retrieval will be lexical, not semantic.",
                exc.__class__.__name__,
            )
            return
        try:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.persist_dir))
            # Cosine space, so distance == 1 - cosine_similarity.
            opts = {"metadata": {"hnsw:space": "cosine"}}
            self._adrs = self._client.get_or_create_collection(ADR_COLLECTION, **opts)
            self._diffs = self._client.get_or_create_collection(DIFF_COLLECTION, **opts)
            self.backend = "chroma"
            log.info("chroma backend ready at %s", self.persist_dir)
        except Exception as exc:  # pragma: no cover
            log.warning("chroma init failed (%s) - using the lexical fallback", exc)
            self._client = self._adrs = self._diffs = None
            self.backend = "lexical"

    @property
    def semantic(self) -> bool:
        """True when retrieval is genuinely dense/semantic."""
        return self.backend == "chroma"

    # -- writes --------------------------------------------------------------

    def upsert_decision(self, payload: dict[str, Any]) -> ADR:
        """Validate and store an ADR. Raises ADRValidationError on bad input."""
        adr = validate_adr(payload)
        text, meta = adr.embedding_text(), adr.to_metadata()
        if self.semantic:
            self._adrs.upsert(ids=[adr.id], documents=[text], metadatas=[meta])
        else:
            self._lex_adrs.upsert(adr.id, text, meta)
        log.info("upserted %s (%s) via %s", adr.id, adr.status, self.backend)
        return adr

    def update_status(
        self,
        adr_id: str,
        status: str,
        superseded_by_adr: str | None = None,
        superseded_by_pr: int | None = None,
    ) -> ADR:
        """Transition an ADR's status, preserving every other field."""
        existing = self.get_decision(adr_id)
        if existing is None:
            raise KeyError(f"{adr_id} is not indexed")
        payload = existing.to_dict()
        payload["status"] = status
        if superseded_by_adr is not None:
            payload["superseded_by_adr"] = superseded_by_adr
        if superseded_by_pr is not None:
            payload["superseded_by_pr"] = superseded_by_pr
        return self.upsert_decision(payload)

    # -- reads ---------------------------------------------------------------

    def get_decision(self, adr_id: str) -> ADR | None:
        adr_id = adr_id.strip().upper()
        if self.semantic:
            got = self._adrs.get(ids=[adr_id])
            metas = got.get("metadatas") or []
            return ADR.from_metadata(metas[0]) if metas else None
        meta = self._lex_adrs.get(adr_id)
        return ADR.from_metadata(meta) if meta else None

    def list_decisions(self) -> list[ADR]:
        if self.semantic:
            metas = self._adrs.get().get("metadatas") or []
        else:
            metas = self._lex_adrs.all_metadata()
        adrs = [ADR.from_metadata(m) for m in metas]
        return sorted(adrs, key=lambda a: a.id)

    def count(self) -> int:
        if self.semantic:
            return int(self._adrs.count())
        return len(self._lex_adrs.all_metadata())

    def search_decisions(
        self,
        query: str,
        paths: list[str] | None = None,
        threshold: float = DEFAULT_THRESHOLD,
        limit: int = 5,
        include_superseded: bool = False,
    ) -> list[dict[str, Any]]:
        """Retrieve candidate ADRs above a cosine-similarity threshold.

        Args:
            query: diff summary, issue text, or a natural-language question.
            paths: changed file paths, appended to the query so file scope
                participates in the match.
            threshold: cosine similarity floor (default 0.70).
            limit: max candidates returned.
            include_superseded: include non-ACTIVE records. Detection wants
                False (only live policy binds a PR); explanation wants True
                (history is the answer).

        Returns:
            Dicts of `{adr, similarity, backend, semantic}`, most similar first.
        """
        if paths:
            query = f"{query}\nChanged paths: {' '.join(paths)}"
        if not query.strip() or self.count() == 0:
            return []

        # Over-fetch so post-filtering by status cannot starve the result set.
        fetch = max(limit * 4, 20)
        rows: list[tuple[ADR, float]] = []

        if self.semantic:
            res = self._adrs.query(query_texts=[query], n_results=min(fetch, max(self.count(), 1)))
            metas = (res.get("metadatas") or [[]])[0]
            dists = (res.get("distances") or [[]])[0]
            for meta, dist in zip(metas, dists):
                # Cosine space: similarity = 1 - distance.
                rows.append((ADR.from_metadata(meta), 1.0 - float(dist)))
        else:
            for _doc_id, sim, meta in self._lex_adrs.query(query, fetch):
                rows.append((ADR.from_metadata(meta), float(sim)))

        out: list[dict[str, Any]] = []
        for adr, sim in rows:
            if not include_superseded and adr.status != "ACTIVE":
                continue
            if sim < threshold:
                continue
            out.append(
                {
                    "adr": adr.to_dict(),
                    "similarity": round(sim, 4),
                    "backend": self.backend,
                    "semantic": self.semantic,
                }
            )
        out.sort(key=lambda r: r["similarity"], reverse=True)
        return out[:limit]

    # -- diff embeddings -----------------------------------------------------

    def upsert_diff(self, diff_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        """Store a diff embedding in `diff_embeddings` for drift analytics."""
        meta = {k: v for k, v in (metadata or {}).items() if v is not None}
        meta.setdefault("diff_id", diff_id)
        if self.semantic:
            self._diffs.upsert(ids=[diff_id], documents=[text], metadatas=[meta])
        else:
            self._lex_diffs.upsert(diff_id, text, meta)
