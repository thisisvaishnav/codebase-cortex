"""Streamable-HTTP MCP server exposing Codebase Cortex vector memory.

This is the `cortex-vector` MCP server the skills and prompts call. It exposes
the three tools the ingest/detect flow depends on, with names the agent
instructions reference verbatim:

- ``searchDecisions`` — candidate ADR retrieval (cosine >= threshold).
- ``upsertDecision``  — validate and store/supersede an ADR.
- ``updateStatus``    — ACTIVE -> SUPERSEDED lineage transitions.

Plus read helpers for diagnostics (`getDecision`, `listDecisions`, `count`,
`healthcheck`).

Run from the repo root (as `.github/workflows/cortex-ingest.yml` does):

    python -m uvicorn cortex_vector_mcp.server:app --host 127.0.0.1 --port 9001

The endpoint is mounted at ``/mcp`` (the MCP Streamable HTTP path), which is
what ``CORTEX_VECTOR_URL=http://localhost:9001/mcp`` points at.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .explain import explain_query, trace_adr_lineage
from .store import DEFAULT_THRESHOLD, Store

log = logging.getLogger(__name__)

#: Where ChromaDB persists. Override in CI and tests so a run never writes into
#: the repo checkout. The ephemeral runner temp dir keeps every job's store
#: consistent within that single ingest/audit run.
PERSIST_DIR = os.environ.get("CORTEX_CHROMA_DIR", "./chromadb_data")

_store: Store | None = None


def get_store() -> Store:
    """One store per process, created lazily so a bare import stays cheap."""
    global _store
    if _store is None:
        log.info("opening cortex-vector store at %s", PERSIST_DIR)
        _store = Store(PERSIST_DIR)
        log.info("backend: %s (%s)", _store.backend, "semantic" if _store.semantic else "lexical fallback")
    return _store


mcp = FastMCP("cortex-vector")

# --------------------------------------------------------------------- tools


@mcp.tool()
def searchDecisions(
    query: str,
    paths: list[str] | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    limit: int = 5,
    include_superseded: bool = False,
) -> dict[str, Any]:
    """Retrieve candidate ADRs above a cosine-similarity threshold.

    Args:
        query: diff summary, issue text, or a natural-language question.
        paths: changed file paths (or globs like ``src/cache/**``); appended to
            the query so file scope participates in the match.
        threshold: cosine similarity floor (default 0.70).
        limit: max candidates returned.
        include_superseded: include non-ACTIVE records. Detection wants False
            (only live policy binds a PR); explanation wants True.

    Returns:
        `{"candidates": [{adr, similarity, backend, semantic}, ...]}` (most
        similar first) plus `count`. Wrapped in an object on purpose: FastMCP
        v1 flattens a returned list into one content block per item, which
        turns a single candidate into a bare object - an object wrapper keeps
        the shape stable for every caller.
    """
    candidates = get_store().search_decisions(
        query, paths=paths, threshold=threshold, limit=limit, include_superseded=include_superseded
    )
    return {"candidates": candidates, "count": len(candidates)}


@mcp.tool()
def explainDecision(
    query: str,
    paths: list[str] | None = None,
    threshold: float = 0.50,
) -> dict[str, Any]:
    """Execute natural language Q&A query over ADR lineage (cortex-explain)."""
    return explain_query(get_store(), query=query, paths=paths, threshold=threshold)


@mcp.tool()
def traceLineage(adr_id: str) -> dict[str, Any]:
    """Trace multi-hop lineage (oldest -> newest) for a specific ADR ID."""
    chain = trace_adr_lineage(get_store(), adr_id=adr_id)
    return {"adr_id": adr_id, "chain": [a.to_dict() for a in chain], "count": len(chain)}


@mcp.tool()
def upsertDecision(adr: dict[str, Any]) -> dict[str, Any]:
    """Validate and store an ADR, keyed on its id (re-running is safe).

    Args:
        adr: `{id, title, author, date, status, reasoning, scope_files,
            invariants, alternatives, merged_pr, ...}`. See
            `cortex_vector_mcp.schema.ADR` for the full field list.

    Returns:
        The validated, stored ADR.
    """
    return get_store().upsert_decision(adr).to_dict()


@mcp.tool()
def updateStatus(
    adr_id: str,
    status: str,
    superseded_by_adr: str | None = None,
    superseded_by_pr: int | None = None,
) -> dict[str, Any]:
    """Transition an ADR's status (e.g. ACTIVE -> SUPERSEDED).

    Preserves every other field so lineage history survives a transition.

    Args:
        adr_id: the record to mutate, e.g. ``ADR-002``.
        status: one of ACTIVE | SUPERSEDED | DEPRECATED | PROPOSED.
        superseded_by_adr: replacement record, e.g. ``ADR-004``.
        superseded_by_pr: PR number that did the superseding.
    """
    return get_store().update_status(
        adr_id, status, superseded_by_adr=superseded_by_adr, superseded_by_pr=superseded_by_pr
    ).to_dict()


@mcp.tool()
def getDecision(adr_id: str) -> dict[str, Any] | None:
    """Fetch one ADR by id, or None if it is not indexed."""
    adr = get_store().get_decision(adr_id)
    return adr.to_dict() if adr else None


@mcp.tool()
def listDecisions(include_superseded: bool = True) -> list[dict[str, Any]]:
    """List every indexed ADR, ordered by id."""
    return [adr.to_dict() for adr in get_store().list_decisions()]


@mcp.tool()
def count() -> int:
    """Number of ADRs currently indexed."""
    return get_store().count()


@mcp.tool()
def healthcheck() -> dict[str, Any]:
    """Report backend name, semantic mode, record count and persist dir.

    Handy for `actions/health` probes and for CI logs deciding whether
    retrieval is dense (chroma) or the stdlib lexical fallback.
    """
    store = get_store()
    return {
        "ok": True,
        "backend": store.backend,
        "semantic": store.semantic,
        "count": store.count(),
        "persist_dir": str(store.persist_dir),
    }


# ------------------------------------------------------------------- export


#: ASGI app for `uvicorn cortex_vector_mcp.server:app`. Rooted at /mcp.
app = mcp.streamable_http_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def api_explain_endpoint(request: Request) -> JSONResponse:
    """HTTP REST endpoint for cortex-explain query engine (used by CLI / Web Dashboard)."""
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}
        query = body.get("question") or body.get("query") or ""
        paths = body.get("paths")
        threshold = float(body.get("threshold", 0.50))
    else:
        query = request.query_params.get("question") or request.query_params.get("q") or ""
        paths_param = request.query_params.get("paths")
        paths = paths_param.split(",") if paths_param else None
        threshold = float(request.query_params.get("threshold", 0.50))

    res = explain_query(get_store(), query=query, paths=paths, threshold=threshold)
    return JSONResponse(res)


async def api_health_endpoint(request: Request) -> JSONResponse:
    """HTTP REST endpoint for health checks."""
    return JSONResponse(healthcheck())


async def api_decisions_endpoint(request: Request) -> JSONResponse:
    """HTTP REST endpoint for listing decisions."""
    inc_param = request.query_params.get("include_superseded", "true").lower()
    include_superseded = inc_param in ("true", "1", "yes")
    return JSONResponse(listDecisions(include_superseded=include_superseded))


async def api_lineage_endpoint(request: Request) -> JSONResponse:
    """HTTP REST endpoint for tracing lineage."""
    adr_id = request.path_params.get("adr_id") or request.query_params.get("adr_id", "")
    return JSONResponse(traceLineage(adr_id=adr_id))


app.add_route("/api/explain", api_explain_endpoint, methods=["GET", "POST"])
app.add_route("/api/health", api_health_endpoint, methods=["GET"])
app.add_route("/api/decisions", api_decisions_endpoint, methods=["GET"])
app.add_route("/api/lineage/{adr_id}", api_lineage_endpoint, methods=["GET"])