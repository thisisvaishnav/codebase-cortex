# TrueForge v0.1.4 — Verified Runtime Findings

> Empirically verified on 2026-08-29 against `@truefoundry/trueforge@0.1.4` (Node v22.23.2, darwin).
> Source of truth: `GET http://localhost:8790/api/v1/openapi.json` + `--help` + live probes.
>
> **This document records where the repo's current design assumes an API that does not exist.**
>
> **Status (2026-08-29):** Findings §1 (no CLI runner), §3 (`agent.json` schema) and §6-8 (broken
> CI workflows) are **resolved**. The repo ships `bin/cortex`, a thin REST wrapper validated
> against the live OpenAPI, and the workflows drive it (`cortex detect|ingest`). The vector
> store, which §4 said could not be an MCP connector, is now a self-hosted Streamable-HTTP
> MCP server under `cortex-vector-mcp/`. The findings below remain the verified *historical*
> basis those decisions were made on.

---

## 1. There is no CLI runner

```
$ npx @truefoundry/trueforge --help
Usage:
  npx @truefoundry/trueforge
  npx @truefoundry/trueforge --port <n>
Options:
  --port <n>   HTTP port (default: 8790, or PORT env)
  -h, --help   Show this help
```

```
$ npx @truefoundry/trueforge run agent.json --skill skills/cortex-detect --input "test"
TypeError [ERR_PARSE_ARGS_UNEXPECTED_POSITIONAL]: Unexpected argument 'run'.
This command does not take positional arguments
```

**Impact:** both CI workflows are non-functional as written.
`.github/workflows/cortex-detect.yml:43` and `.github/workflows/cortex-ingest.yml:34` both invoke
`npx @truefoundry/trueforge run agent.json --skill … --input …`. That command errors out immediately.

TrueForge is a **server**, driven over REST. `agent.json` is not a CLI input artifact.

**Resolution (2026-08-29):** `bin/cortex` is a thin REST wrapper (`./bin/cortex ingest --pr <n>`,
`detect`, `explain`, `setup`, `doctor`). Both workflows now start TrueForge on :8790 and drive
`/api/v1` through it, provisioning model providers, MCP servers and git-backed skills per run.

---

## 2. The real control surface (REST, `/api/v1`)

| Purpose | Endpoint |
|---|---|
| Create/list/update/delete saved agent | `POST|GET|PUT|DELETE /agents[/{id}]` |
| Start a session (agent by name, or inline spec) | `POST /sessions` |
| **Run the agent** (one turn) | `POST /sessions/{id}/turns` |
| Stream turn output (SSE) | `GET /sessions/{id}/turns/{turn_id}/subscribe` |
| Turn/session event history | `GET /sessions/{id}/events`, `…/turns/{turn_id}/events` |
| Configure model providers | `GET|POST|PUT /settings/model-providers` |
| Configure MCP servers | `GET|POST|PUT /settings/mcp-servers` |
| Configure skills | `GET|POST|PUT /settings/skills` |
| Configure sandbox provider | `GET|PUT /settings/sandbox-providers` |
| Browse built-in catalogs | `GET /catalogs/{skills,mcp-servers,model-providers,sandbox-providers}` |
| Interactive docs | `GET /api/v1/docs` |

Persistent state confirmed at:
`~/Library/Application Support/trueforge/db/db.sqlite` (standalone mode, SQLite, no Redis).

---

## 3. `agent.json` does not match the real `AgentSpec`

Real schema — `CreateAgentRequest { name, manifest: AgentSpec }`, where `AgentSpec` is:

```jsonc
{
  "model":        { "name": "openai/gpt-5.5", "params": { /* ModelParams */ } }, // REQUIRED, FQN form
  "instructions": "…",                    // optional system prompt
  "messages":     [ { "type": "user.message", "content": "…" } ],
  "mcp_servers":  [ { "name": "github", "enable_tools": ["@all"] } ],  // name-only refs
  "skills":       [ { "name": "cortex-detect" } ],                     // name-only refs
  "response_format": { /* … */ },
  "config": {
    "iteration_limit": 100,
    "sandbox":            { "enabled": false, "file_downloads": true },
    "dynamic_sub_agents": { "enabled": true },
    "context_management": { "compaction": {"enabled": true}, "large_tool_response": {"enabled": true} },
    "generative_ui":      { "enabled": true },
    "ask_user_questions": { "enabled": true }
  }
}
```

Gap analysis against the committed `agent.json`:

| Current `agent.json` | Reality |
|---|---|
| `model: {provider, modelName, temperature}` | ✗ Must be `model: {name: "openai/<model>", params: {...}}` |
| `connectors: [{id, name, type:"mcp", config:{command, args}}]` | ✗ No such key. Use `mcp_servers: [{name}]` — **name-only references to servers already configured in Settings** |
| `skills: ["skills/cortex-detect", …]` | ✗ Must be `skills: [{name: "cortex-detect"}]`. `Skill.name` pattern is `^[A-Za-z0-9._-]+$` — a `/` is **invalid** |
| `subAgents: [ {name, role, skills}, … ]` (4 named) | ✗ No such key. Only `config.dynamic_sub_agents.enabled: true` — subagents are spawned dynamically by the agent, not declared |
| `sandbox: {provider:"daytona", enabled:true}` | ✗ Must be `config.sandbox.enabled: true`; provider is set globally via `PUT /settings/sandbox-providers` |
| `name`, `displayName`, `description`, `version` | ✗ Not in `AgentSpec`. Agent name belongs in `CreateAgentRequest.name` |
| `model.modelName: "gpt-4o"` | ⚠ Not in the current catalog (which lists `gpt-5.5`, `gpt-5.4-mini`, `gpt-5.6-luna`, …) |

**Also note:** `skills` **requires `config.sandbox.enabled: true`**. Skills are materialised as
directories in the sandbox — so no sandbox means no skills.

---

## 4. Only **remote** MCP servers are supported

```jsonc
"MCPServerType": { "type": "string", "enum": ["remote"] }
```

There is no stdio / `command` + `args` transport. This invalidates all three planned connectors
as specified:

| Planned connector | Status |
|---|---|
| GitHub via `npx @modelcontextprotocol/server-github` (stdio) | ✗ stdio unsupported — **but** a remote `github` MCP exists in the catalog: `https://api.githubcopilot.com/mcp/` ✓ |
| Filesystem via `npx @modelcontextprotocol/server-filesystem` (stdio) | ✗ No filesystem MCP at all. ADR file I/O must go through the **sandbox** instead |
| ChromaDB / VectorStore MCP | ✗ Not in the catalog, and no stdio option. Must either run as code **inside the sandbox**, or be a remote MCP we host ourselves |

Full built-in catalog (all `remote`): `linear`, `notion`, `sentry`, `deepwiki`, `exa`,
`parallel-web`, `github`, `tavily`, `bright-data`, `supabase`, `stripe`, `confluence`, `jira`,
`posthog`.

Custom remote servers can be registered via `POST /settings/mcp-servers` (auth: `header` or `dcr`).

---

## 5. What *does* work in our favour

- **Sandbox works with no Daytona account.** Server log: `Local sandbox fallback is available
  {"platform":"darwin","shell":"/opt/homebrew/bin/bash","python":".../python3.14"}`.
  Daytona remains configurable via `PUT /settings/sandbox-providers` (catalog confirms `daytona`).
- **SSE streaming exists** (`GET /sessions/{id}/turns/{turn_id}/subscribe`) — a real transport for
  the dashboard's live violation feed, exactly as the architecture wanted.
- **Dynamic sub-agents are on by default** (`config.dynamic_sub_agents.enabled: true`).
- **Skills are a first-class, configurable resource** (`/settings/skills`, `/catalogs/skills`), and
  the catalog is git-backed — matching how `skills/*/SKILL.md` is already authored.
- **GitHub MCP is genuinely available**, remotely, which covers the diff/comment/issue/CODEOWNERS
  needs of `cortex-detect`, `cortex-ingest`, and `cortex-notify`.

---

## 6. Consequences for TASKS.md

| Task | Consequence |
|---|---|
| 1 — Core harness & MCP connectors | Rewrite `agent.json` to `AgentSpec`; connectors reduce to remote `github` only — **done** |
| 2 — Vector store | Cannot be an MCP connector. Runs as sandbox code, or self-hosted remote MCP — **done**: self-hosted `cortex-vector-mcp/` Streamable-HTTP MCP server (`searchDecisions`, `upsertDecision`, `updateStatus`) |
| 3, 4, 5, 6 — the four cortex skills | Skills are **LLM instruction packs run in a sandbox**, not invocable code modules. Needs a decision on where real logic (embeddings, cosine similarity) lives — logic now lives in `cortex-vector-mcp/` |
| 7 — Qodo resolver | Unaffected in principle (Qodo is a separate GitHub Action) |
| 8 — CI workflows | **Broken.** Must drive the REST API, or wrap it in a CLI of our own — **done**: `bin/cortex` REST wrapper, used by both workflows |
| 9 — Dashboard | Wire to `POST /sessions`, `POST …/turns`, `GET …/subscribe` (SSE) |
| 10 — Daytona sandbox | Feasible; local fallback available for the demo |
| 11 — Demo scenarios | Depends on all of the above |
