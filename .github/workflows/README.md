# Codebase Cortex — GitHub Actions workflows

Two workflows drive the agent from CI. Both treat TrueForge v0.1.4 as a **server**
(`npx @truefoundry/trueforge --port 8790`), not a CLI — there is no `trueforge run`.
See `docs/TRUEFORGE-API-FINDINGS.md` for the verified gap analysis, and
`bin/cortex` for the REST wrapper both workflows use.

| Workflow | Trigger | Purpose |
|---|---|---|
| `cortex-ingest.yml` | `pull_request` `closed` with `merged == true` | Capture a merged decision as `docs/adr/ADR-XXX-<slug>.md`, index it into vector memory, mark superseded ADRs, post a confirmation comment |
| `cortex-detect.yml` | `pull_request` (opened, synchronize) and `issues` (opened) | Two-stage contradiction audit of diffs/issues against ACTIVE ADRs; upserts one comment per thread |

## Services started per run

1. **TrueForge** on `:8790` — the agent runtime (session/turn REST API).
2. **cortex-vector** on `:9001` — a FastMCP Streamable-HTTP server
   (`cortex-vector-mcp/`, endpoint `/mcp`) exposing `searchDecisions`,
   `upsertDecision`, `updateStatus`. Its Chroma store is seeded from `docs/adr/`
   by the cold-start indexer on every run.

## Secrets / vars required

| Name | Needed for | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` | TrueForge model provider | At least one is required, or ingest/detect aborts |
| `CORTEX_GITHUB_PAT` | the remote **github** MCP | `api.githubcopilot.com/mcp/` may reject the ephemeral Actions token; a PAT is the reliable path. Falls back to `GITHUB_TOKEN`. |
| `GITHUB_TOKEN` | checkout + fallback | Auto-provided by Actions |
| `TF_API_KEY` | TrueForge auth | Optional: standalone mode runs with auth disabled |
| `CHROMA_API_KEY` / `OPENAI_API_KEY` (vector) | cortex-vector embeddings | Only needed for Chroma Cloud / remote embedding APIs; local Chroma uses bundled MiniLM |
| `vars.CORTEX_MODEL` | model override | Default `anthropic/claude-sonnet-5` |

Set these in **Repository → Settings → Secrets and variables → Actions**.

## Local dry-run

```bash
# 1. vector memory
cd cortex-vector-mcp
python -m pip install -r requirements.txt
python -m uvicorn cortex_vector_mcp.server:app --port 9001 &
CORTEX_CHROMA_DIR=/tmp/cortex-chroma python -m cortex_vector_mcp.indexer \
  --adr-dir ../docs/adr --persist-dir /tmp/cortex-chroma

# 2. TrueForge + the CLI wrapper
npx @truefoundry/trueforge --port 8790 &
TF_URL=http://localhost:8790 ./bin/cortex doctor

# 3. a real run needs a merged PR and the GitHub/github tokens; for a shape-only
#    smoke test of the prompt and session plumbing, run with a real PR number:
GITHUB_TOKEN=... ./bin/cortex ingest --pr 118 --author senior-dev
```