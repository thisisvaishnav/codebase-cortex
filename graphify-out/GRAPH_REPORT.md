# Graph Report - codebase-cortex  (2026-08-30)

## Corpus Check
- Corpus is ~42,414 words - fits in a single context window. You may not need a graph.

## Summary
- 504 nodes · 793 edges · 42 communities (22 shown, 20 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 49 edges (avg confidence: 0.9)
- Token cost: 9,800 input · 3,200 output

## Community Hubs (Navigation)
- ADR Indexer & Parser
- Sandbox Fitness Functions
- NL Explain & Lineage Engine
- GitHub Actions CI Pipeline
- Dashboard UI (React/Vite)
- React App Components
- Demo & Test Suite
- bin/cortex REST Wrapper
- Demo Ingest Scenario Files
- Redis Session Store (src/cache)
- Skills & Hackathon Docs
- Notify & Comment Engine
- Demo Violation Scenario Files
- Lexical Index Fallback
- Banned Dependency Checker
- ChromaDB Vector Store
- ADR Schema & Validation
- Detect & Audit Agent
- Ingest & Memory Agent
- CODEOWNERS & Maintainers
- MCP Server Tools
- Qodo PR Resolver Skill
- Dashboard Q&A Query Flow
- Architectural Drift Concepts
- GitHub MCP Integration
- Token Revocation & JWT
- Demo Issue Pre-flight
- Python Dependencies
- TrueForge Provisioning
- ADR Lineage & History
- Daytona Sandbox Config
- ADR Vector Search
- PR Comment Deduplication
- Event-Driven Architecture ADR
- Session Touch & Expiry
- Cortex Explain Skill
- Dashboard SVG Assets
- Cortex Detect Skill
- cortex-notify SKILL
- Requirements & Deps
- TrueForge API Findings

## God Nodes (most connected - your core abstractions)
1. `Store` - 32 edges
2. `ADR` - 20 edges
3. `explain_query()` - 13 edges
4. `get_store()` - 13 edges
5. `validate_adr()` - 12 edges
6. `_LexicalIndex` - 11 edges
7. `check_architectural_veto()` - 11 edges
8. `_client()` - 10 edges
9. `QodoFinding` - 10 edges
10. `resolve_qodo_findings()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `cortex-explain Institutional Q&A Subagent` --semantically_similar_to--> `executeQuery() - Institutional Memory Query to port 9001/api/explain`  [INFERRED] [semantically similar]
  TASKS.md → dashboard.html
- `check_architectural_veto()` --uses--> `ADR`  [INFERRED]
  sandbox/qodo/qodo_resolver.py → cortex-vector-mcp/cortex_vector_mcp/schema.py
- `format_inline_reply()` --uses--> `ADR`  [INFERRED]
  sandbox/qodo/qodo_resolver.py → cortex-vector-mcp/cortex_vector_mcp/schema.py
- `run_scenario_1()` --uses--> `Store`  [INFERRED]
  demo/run_demo_suite.py → cortex-vector-mcp/cortex_vector_mcp/store.py
- `run_scenario_2()` --uses--> `Store`  [INFERRED]
  demo/run_demo_suite.py → cortex-vector-mcp/cortex_vector_mcp/store.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **CI/CD Architectural Guard & Ingest Pipeline** — cortex_vector_mcp_requirements_dependencies [EXTRACTED 1.00]
- **Codebase Cortex ADR System & Invariants** — docs_adr_001_codebase_cortex_adr001, docs_adr_adr_002_distributed_cache_redis_adr002, docs_adr_adr_003_event_driven_architecture_adr003 [EXTRACTED 1.00]
- **Hackathon Overview, Rules, and Prizes Suite** — hackathon_docs_00_index_index_doc, hackathon_docs_01_overview_overview_doc, hackathon_docs_02_rules_rules_doc, hackathon_docs_03_prizes_prizes_doc [EXTRACTED 1.00]
- **TrueForge Agent Execution and Runtime Infrastructure** — hackathon_docs_04_trueforge_getting_started_trueforge_harness, hackathon_docs_04_trueforge_getting_started_mcp_tools, hackathon_docs_04_trueforge_getting_started_daytona_sandbox, hackathon_docs_04_trueforge_getting_started_sub_agents [EXTRACTED 1.00]
- **Codebase Cortex Architectural Governance & Memory Loop** — skills_cortex_detect_skill_cortex_detect_workflow, skills_cortex_ingest_skill_cortex_ingest_skill, skills_cortex_explain_skill_cortex_explain_skill, skills_cortex_notify_skill_cortex_notify_skill [EXTRACTED 1.00]
- **Qodo Code Quality, Standards & Automated Remediation** — skills_qodo_get_rules_skill_qodo_get_rules_skill, skills_qodo_pr_resolver_skill_qodo_pr_resolver_skill, skills_qodo_pr_resolver_skill_architectural_veto_gate, skills_qodo_pr_resolver_reference_pr_resolver_templates [EXTRACTED 1.00]
- **Cortex Detect Violation Detection Pipeline** — _github_workflows_cortex_detect_yml_cortex_detect_workflow, tasks_md_cortex_detect_two_stage_engine, _github_workflows_cortex_detect_yml_cortex_vector_mcp, _github_workflows_cortex_detect_yml_github_mcp_server, concept_pr_comment_upsert_deduplication [INFERRED 0.90]
- **Cortex Ingest ADR Capture & Vector Indexing Pipeline** — _github_workflows_cortex_ingest_yml_cortex_ingest_workflow, _github_workflows_cortex_ingest_yml_adr_seed_indexer, tasks_md_adr_vector_store, _github_workflows_cortex_ingest_yml_bin_cortex_ingest, concept_adr_institutional_memory [INFERRED 0.92]
- **Dashboard Q&A Query-to-Render Flow** — dashboard_html_execute_query, dashboard_html_render_result, dashboard_html_fetch_adr_timeline, dashboard_html_render_adr_timeline, _github_workflows_cortex_detect_yml_cortex_vector_mcp [EXTRACTED 0.95]

## Communities (42 total, 20 thin omitted)

### Community 0 - "ADR Indexer & Parser"
Cohesion: 0.07
Nodes (37): _bullets(), _extract_paths(), index_directory(), main(), parse_adr_markdown(), Any, Cold-start indexer: parse `docs/adr/ADR-*.md` into the vector store. The ADRs…, Parse one ADR markdown file into an unvalidated payload dict. (+29 more)

### Community 1 - "Sandbox Fitness Functions"
Cohesion: 0.06
Nodes (48): dict, Exception, build_parser(), call_matches(), compile_patterns(), dotted_name(), emit(), FitnessError (+40 more)

### Community 2 - "NL Explain & Lineage Engine"
Cohesion: 0.09
Nodes (36): explain_query(), format_explain_response(), Any, Institutional Q&A & Multi-Hop Lineage Reasoning Engine for cortex-explain.…, Execute natural language Q&A query over ADR lineage. Args: store: vector store.…, Walk an ADR's lineage in both directions to reconstruct its full history. Args:…, Format a contextual response attributing decisions to authors, dates, and…, trace_adr_lineage() (+28 more)

### Community 3 - "GitHub Actions CI Pipeline"
Cohesion: 0.07
Nodes (36): bin/cortex detect CLI Command, Cortex Detect GitHub Actions Workflow, Cortex Vector MCP Service (port 9001), GitHub MCP Remote Server (api.githubcopilot.com/mcp/), Qodo PR Agent Code Review, TrueForge Skills Provisioning (cortex-detect, cortex-ingest, cortex-notify, cortex-explain, qodo-get-rules, qodo-pr-resolver), TrueForge REST Server (port 8790), ADR Cold-Start Seed Indexer (cortex_vector_mcp.indexer) (+28 more)

### Community 4 - "Dashboard UI (React/Vite)"
Cohesion: 0.06
Nodes (35): clsx, dependencies, clsx, lucide-react, react, react-dom, tailwind-merge, devDependencies (+27 more)

### Community 5 - "React App Components"
Cohesion: 0.13
Nodes (23): App(), pollHealth(), ExplainConsole(), handleSampleClick(), handleSearch(), SAMPLE_QUESTIONS, Header(), LineageGraph() (+15 more)

### Community 6 - "Demo & Test Suite"
Cohesion: 0.16
Nodes (21): main(), print_banner(), Codebase Cortex — Hackathon Demo & Verification Suite. Runs end-to-end…, run_scenario_1(), run_scenario_2(), run_scenario_3(), run_scenario_4(), check_architectural_veto() (+13 more)

### Community 7 - "bin/cortex REST Wrapper"
Cohesion: 0.20
Nodes (22): api(), authHeaders(), die(), doctor(), ensureAgent(), ensureGithubMcp(), ensureSkills(), ensureVectorMcp() (+14 more)

### Community 8 - "Demo Ingest Scenario Files"
Cohesion: 0.15
Nodes (19): _client(), create_session(), delete_session(), get_session(), healthcheck(), is_token_revoked(), iter_sessions(), Any (+11 more)

### Community 9 - "Redis Session Store (src/cache)"
Cohesion: 0.15
Nodes (19): _client(), create_session(), delete_session(), get_session(), healthcheck(), is_token_revoked(), iter_sessions(), Any (+11 more)

### Community 10 - "Skills & Hackathon Docs"
Cohesion: 0.11
Nodes (20): qodo-get-rules Skill Overview, qodo-pr-resolver Skill Overview, Cortex Detect Architectural Contradiction Analysis, Single-Comment Upsert Strategy, Two-Stage Retrieval and Evaluation Pipeline, Cortex Explain Knowledge Q&A Skill, Multi-Hop ADR Lineage Tracing, Cortex Ingest Knowledge Synchronization Skill (+12 more)

### Community 11 - "Notify & Comment Engine"
Cohesion: 0.17
Nodes (17): clean_handle(), compute_content_hash(), format_comment(), main(), match_path(), normalize_markdown(), parse_codeowners_rules(), Normalise markdown body for sha256 content hashing. (+9 more)

### Community 12 - "Demo Violation Scenario Files"
Cohesion: 0.15
Nodes (11): create_session(), get_session(), healthcheck(), iter_sessions(), Any, RuntimeError, In-process session and token-revocation store. Replaces the Redis-backed…, Kept for API compatibility. The in-process store cannot fail this way. (+3 more)

### Community 13 - "Lexical Index Fallback"
Cohesion: 0.21
Nodes (6): _LexicalIndex, Any, Store a diff embedding in `diff_embeddings` for drift analytics., Lowercase word tokens, plus path components split on separators.…, Minimal TF-IDF cosine index. Rebuilds on write; the corpus is tiny., _tokenize()

### Community 14 - "Banned Dependency Checker"
Cohesion: 0.27
Nodes (7): _check_banned_calls(), _check_banned_modules(), _check_in_process_state(), _is_container_type(), run(), main(), run_all()

### Community 16 - "ADR Schema & Validation"
Cohesion: 0.25
Nodes (7): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, warn

### Community 17 - "Detect & Audit Agent"
Cohesion: 0.29
Nodes (7): Daytona Code Execution Sandbox, Model Context Protocol Tools, TrueForge Agent Harness, TrueForge Agent Cookbook, Hackathon Resources and Official Links, Architectural Fitness Verification Checks, Sandbox Patch Verification and Iteration Loop

### Community 18 - "Ingest & Memory Agent"
Cohesion: 0.33
Nodes (6): PR Decision Record Template, ADR-001: Codebase Cortex Architecture Decision, Two-Stage Contradiction Detection Engine, ADR-002: Redis for Distributed Session Persistence, ADR-003: Asynchronous Event Bus for Billing & Notifications, System Architecture Specification

### Community 19 - "CODEOWNERS & Maintainers"
Cohesion: 0.50
Nodes (4): Hackathon Documentation Index, Hackathon Overview and Core Challenge, Hackathon Rules & Requirements, Hackathon Prize Tracks

### Community 20 - "MCP Server Tools"
Cohesion: 0.50
Nodes (3): plugin, $schema, .opencode/plugins/graphify.js

### Community 21 - "Qodo PR Resolver Skill"
Cohesion: 1.00
Nodes (3): Demo Base Requirements, Scenario 1 Ingest Requirements, Scenario 2 Violation Requirements

## Knowledge Gaps
- **63 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `$schema`, `oxc`, `react/rules-of-hooks` (+58 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Store` connect `ADR Indexer & Parser` to `NL Explain & Lineage Engine`, `Lexical Index Fallback`, `Demo & Test Suite`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `ADR` connect `ADR Indexer & Parser` to `NL Explain & Lineage Engine`, `Demo & Test Suite`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `_LexicalIndex` connect `Lexical Index Fallback` to `ADR Indexer & Parser`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Store` (e.g. with `explain_query()` and `trace_adr_lineage()`) actually correct?**
  _`Store` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `ADR` (e.g. with `explain_query()` and `format_explain_response()`) actually correct?**
  _`ADR` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `explain_query()` (e.g. with `ADR` and `Store`) actually correct?**
  _`explain_query()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `$schema` to the rest of the system?**
  _63 weakly-connected nodes found - possible documentation gaps or missing edges._