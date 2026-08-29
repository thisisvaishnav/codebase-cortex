# Tasks

## Active

- [x] **Initialize TrueForge Core Harness & MCP Connectors** - Configure `agent.json` with model provider, tools, and subagents
  - [x] Verify `@truefoundry/trueforge` CLI / SDK installation and runtime — v0.1.4 installs & runs; **no CLI runner exists** (server-only, REST on :8790). See `docs/TRUEFORGE-API-FINDINGS.md`
  - [x] Rewrite `agent.json` to the real `AgentSpec` schema — `{name, manifest:{model, instructions, mcp_servers, skills, config}}` matches `CreateAgentRequest` per the live OpenAPI
  - [x] Configure GitHub MCP connector (`readDiff`, `postComment`, `upsertComment`, `readIssue`, `readCODEOWNERS`) — only the **remote** `github` MCP is usable (`api.githubcopilot.com/mcp/`); registered via `bin/cortex` `ensureGithubMcp` and the workflow's provisioning step (auth shape: `{type:"header", headers:{Authorization: "Bearer …"}}`)
  - [x] ~~Configure VectorStore MCP connector~~ — **not possible as MCP** (no remote Chroma server; stdio unsupported). **Resolved:** self-hosted `cortex-vector-mcp/` FastMCP Streamable-HTTP server (see task 2)
  - [x] ~~Configure Filesystem MCP connector~~ — **not possible as MCP** (no filesystem server in catalog). ADR file I/O goes through the sandbox
  - [x] Validate SQLite persistent state storage across sessions — confirmed at `~/Library/Application Support/trueforge/db/db.sqlite` (standalone mode, no Redis)

- [x] **Build Vector Knowledge Store & ADR Ingestion Engine** - Set up ChromaDB schema and embedding pipeline
  - [x] Initialize ChromaDB local/hosted client with vector collections (`adr_collection`, `diff_embeddings`) — `cortex-vector-mcp/cortex_vector_mcp/store.py`, with a stdlib TF-IDF **lexical fallback** when chromadb is unavailable
  - [x] Implement ADR schema validator (`id`, `title`, `author`, `status`, `scope_files`, `invariants`, `reasoning`, `date`) — `schema.py::validate_adr`
  - [x] Build cold-start indexer to load existing ADRs (`docs/adr/ADR-*.md`) into vector collection — `indexer.py`, wired into `cortex-ingest.yml` as the "Seed ADR vector store" step
  - [x] Implement cosine similarity query interface with threshold calibration (>= 0.70 retrieval) — `Store.search_decisions` (`DEFAULT_THRESHOLD = 0.70`), exposed over MCP as `searchDecisions`

- [x] **Implement `cortex-ingest` Agent & PR Merge Pipeline** - Automate institutional memory capture on merge
  - [x] Build PR decision template parser (`.github/pull_request_template.md` structured fields) — `skills/cortex-ingest/SKILL.md` Path A + prompt `PROMPTS.ingest`
  - [x] Implement fallback LLM extractor for PRs lacking explicit decision template — SKILL Path B (architectural-surface diff check)
  - [x] Implement Git ADR writer saving markdown records to `docs/adr/ADR-XXX-<slug>.md` — SKILL Step 3 (sandbox write; committed with `contents: write`)
  - [x] Implement ADR status transition logic (mark previous decisions as `SUPERSEDED` when overridden) — SKILL Step 5 + `Store.update_status` (`updateStatus` MCP tool)
  - [x] Wire automated post-merge confirmation comment to GitHub PR thread — SKILL Step 6 (`<!-- codebase-cortex:pr-analysis -->` upsert)
  - Note: pipeline pieces verified locally (vector MCP e2e + `node --check`); full runtime needs TrueForge + model key + `CORTEX_GITHUB_PAT` (see `.github/workflows/README.md`)

- [ ] **Implement `cortex-detect` Two-Stage Violation Engine** - Contradiction detection on PR diffs and issues
  - Implement Stage 1: Dense semantic candidate retrieval against modified file paths and diff concepts
  - Implement Stage 2: LLM intent & invariant cross-encoder verification with confidence scoring (>= 80% hard violation, 60-79% advisory)
  - Integrate `qodo-get-rules` pre-flight step to load repo coding standards before audit
  - Implement AST / architectural fitness test execution hook inside Daytona sandbox
  - Build single-comment upsert mechanism (`<!-- codebase-cortex:pr-analysis -->`) to prevent PR notification spam

- [ ] **Implement `cortex-notify` Maintainer Escalation Engine** - Intelligent routing to original authors and CODEOWNERS
  - Build `.github/CODEOWNERS` parser to resolve responsible maintainers for affected paths
  - Implement author resolution from matching ADR metadata (`@senior-dev`, original PR link)
  - Build message formatting engine for drift warnings and contradiction alerts with actionable remediation tips
  - Add deduplication and cooldown logic for PR review comment updates

- [ ] **Implement `cortex-explain` Institutional Q&A Subagent** - Natural language query engine
  - Implement semantic search and multi-hop reasoning over ADR lineage (active vs. superseded)
  - Build contextual response generator attributing decisions to authors, timestamps, and trade-offs
  - Expose query endpoint for CLI and web dashboard consumption

- [ ] **Build Qodo PR Self-Healing Integration (`qodo-pr-resolver`)** - Connect code quality with architecture
  - Ingest Qodo PR review comments and findings (`ERROR`, `WARNING`, `RECOMMENDATION`)
  - Implement automated patch generation resolving code quality issues adhering to architectural invariants
  - Post resolution replies to inline GitHub review threads and push fix commits

- [ ] **Configure GitHub Actions CI Automation Workflows** - Zero-dependency headless execution in CI
  - [x] Build `.github/workflows/cortex-detect.yml` triggering on `pull_request` (opened, synchronize) and `issues` (opened) — drives the agent through `bin/cortex detect`
  - [x] Build `.github/workflows/cortex-ingest.yml` triggering on `pull_request` (closed, merged=true) — runs `bin/cortex ingest --pr <n>`, provisions TrueForge + vector MCP, seeds the store
  - [x] Replace both run steps with a working invocation path — our own CLI wrapper `bin/cortex` drives `/api/v1` directly (verified against the live OpenAPI; see `docs/TRUEFORGE-API-FINDINGS.md`)
  - [ ] Configure GitHub secrets (`ANTHROPIC_API_KEY`/`OPENAI_API_KEY`, `CORTEX_GITHUB_PAT`, `TF_API_KEY`, `CHROMA_API_KEY`) and confirm `actions/cache` keys — set these in repo Settings; see `.github/workflows/README.md`

- [ ] **Develop Web Dashboard & Visual Lineage UI** - Interactive frontend for visualization and demo
  - Scaffold React + Tailwind CSS dashboard project (Vite / Next.js)
  - Build interactive ADR Visual Timeline & Superseded Lineage graph
  - Build Real-time Maintainer Violation & Drift Feed component
  - Build NL Question-Answering console ("Why did we choose Redis over Postgres?")
  - Wire REST / SSE communication to local TrueForge daemon on port `8790`

- [ ] **Configure Daytona Sandbox Environment** - Isolated runtime for safe execution
  - Configure Daytona workspace definition for architectural fitness function execution
  - Write sample fitness test scripts checking import boundaries and banned dependencies
  - Connect sandbox execution bridge to `cortex-detect` evaluation flow

- [ ] **Prepare Test Scenarios & Hackathon Demo Suite** - End-to-end verification
  - Create Demo Scenario 1: Senior dev merges PR introducing Redis cache -> ADR-002 auto-indexed
  - Create Demo Scenario 2: Junior dev opens PR replacing Redis with in-memory map -> `cortex-detect` flags violation, tags `@senior-dev`
  - Create Demo Scenario 3: Contributor opens Issue proposing architecture change -> pre-flight warning posted
  - Create Demo Scenario 4: Natural language queries on Dashboard demonstrating decision recall and lineage

## Waiting On

- [x] **Direction on TrueForge integration shape** — the repo's design assumes a `trueforge run agent.json --skill X --input Y` CLI and three stdio MCP connectors. **None of these exist in v0.1.4.** Full verified gap analysis in `docs/TRUEFORGE-API-FINDINGS.md`. Needs a call on: (a) how CI invokes the agent, (b) where the vector-search logic lives, (c) which tasks to prioritise before the deadline.

## Someday

- [ ] **Multi-repo Architectural Federation** - Share and enforce architectural decisions across microservice repositories
- [ ] **Slack / Discord Webhook Notifications** - Direct DM escalation for high-severity architectural conflicts
- [ ] **Automated Architecture Drift Heatmaps** - Visual codebase heatmap showing files diverging from documented ADRs

## Done
