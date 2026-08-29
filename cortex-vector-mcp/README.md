# cortex-vector-mcp

ADR vector memory for Codebase Cortex, exposed as an MCP server.

## What this is

`docs/adr/ADR-*.md` are the project's institutional memory; this package is the
retrieval half. It validates ADR payloads, stores them (ChromaDB cosine index by
default, a stdlib TF-IDF fallback when chromadb cannot import), seeds itself
from the markdown files via the cold-start indexer, and serves the records to
agents over MCP:

| MCP tool | Purpose |
|---|---|
| `searchDecisions(query, paths?, threshold?, limit?, include_superseded?)` | Candidate ADRs above a cosine threshold; filters SUPERSEDED records out of the default (detection) view. Voice of `cortex-detect` and `cortex-explain`. |
| `upsertDecision(adr)` | Validate + store (keyed on `id`; re-running is safe). |
| `updateStatus(adr_id, status, superseded_by_adr?, superseded_by_pr?)` | ACTIVE → SUPERSEDED lineage transitions for `cortex-ingest`. |
| `getDecision / listDecisions / count / healthcheck` | Diagnostics. |

## Layout

- `cortex_vector_mcp/schema.py` — `ADR` dataclass + `validate_adr` (the single
  gate everything enters the store through)
- `cortex_vector_mcp/store.py` — `Store`: chroma `adr_collection` /
  `diff_embeddings` with lexical fallback; `DEFAULT_THRESHOLD = 0.70`
- `cortex_vector_mcp/indexer.py` — cold-start loader for `docs/adr/ADR-*.md`
- `cortex_vector_mcp/server.py` — FastMCP Streamable-HTTP server (`app`),
  endpoint mounted at `/mcp`

## Run

```bash
python -m pip install -r requirements.txt            # mcp (v1), uvicorn, chromadb
python -m uvicorn cortex_vector_mcp.server:app --host 127.0.0.1 --port 9001

# in a second shell: seed existing ADRs (same CORTEX_CHROMA_DIR as the server)
CORTEX_CHROMA_DIR=/tmp/cortex-chroma python -m cortex_vector_mcp.indexer \
  --adr-dir ../docs/adr --persist-dir /tmp/cortex-chroma
```

Env: `CORTEX_CHROMA_DIR` (persist dir, default `./chromadb_data`),
`CORTEX_FORCE_LEXICAL=1` (skip chromadb), `CHROMA_API_KEY`,
`OPENAI_API_KEY` (for the store's own embeddings if configured).

The first chroma embedding downloads `all-MiniLM-L6-v2` (~80MB) into
`~/.cache/chroma`; both CI workflows cache that directory so the download
happens once per runner. Retrieval quality is reported honestly per call via
`{backend, semantic}` — when `semantic: false`, matches are lexical and the
0.70 default threshold will rarely be met, which is by design.