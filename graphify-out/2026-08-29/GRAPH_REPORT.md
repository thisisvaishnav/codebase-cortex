# Graph Report - codebase-cortex  (2026-08-29)

## Corpus Check
- Corpus is ~37,200 words - fits in a single context window. You may not need a graph.

## Summary
- 267 nodes · 420 edges · 23 communities (12 shown, 11 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Vector Indexer & Store
- Architectural Fitness & Rule Enforcement
- CLI Tooling & Environment Setup
- Distributed Session Storage
- Vector MCP Server & API Endpoints
- Cortex Agent Skills & Workflows
- Session Storage Fixtures & Demo Modules
- Lexical & Vector Search Store
- Architecture Decision Records & Event Bus
- TrueForge Sandbox & Execution Harness
- Hackathon Guidelines & Resources
- Demo Scenario Requirements & Fixtures
- OpenCode Graphify Plugin Integration
- Base Cache Module Specifications
- Ingest Cache Module Specifications
- Violation Cache Module Specifications
- Qodo Code Review & Evidence
- Shift-Left Governance Rationale
- Codebase Cortex Dashboard UI
- Dynamic Sub-agent Workflows
- Agentic PR Review Commands
- Cortex Explain Query Interface
- PR Resolution Summary Comments

## God Nodes (most connected - your core abstractions)
1. `Store` - 18 edges
2. `ADR` - 14 edges
3. `validate_adr()` - 12 edges
4. `_LexicalIndex` - 11 edges
5. `get_store()` - 10 edges
6. `_client()` - 10 edges
7. `ADRValidationError` - 9 edges
8. `normalise()` - 9 edges
9. `parse_adr_markdown()` - 8 edges
10. `index_directory()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `cortex-detect Workflow` --references--> `Cortex Vector MCP Dependencies`  [EXTRACTED]
  .github/workflows/cortex-detect.yml → cortex-vector-mcp/requirements.txt
- `cortex-ingest Workflow` --references--> `Cortex Vector MCP Dependencies`  [EXTRACTED]
  .github/workflows/cortex-ingest.yml → cortex-vector-mcp/requirements.txt
- `Architectural Fitness Verification Checks` --conceptually_related_to--> `Daytona Code Execution Sandbox`  [INFERRED]
  skills/cortex-detect/SKILL.md → hackathon-docs/04-trueforge-getting-started.md
- `Sandbox Patch Verification and Iteration Loop` --conceptually_related_to--> `Daytona Code Execution Sandbox`  [INFERRED]
  skills/qodo-pr-resolver/SKILL.md → hackathon-docs/04-trueforge-getting-started.md
- `PR Decision Record Template` --conceptually_related_to--> `ADR-001: Codebase Cortex Architecture Decision`  [EXTRACTED]
  .github/pull_request_template.md → docs/ADR-001-codebase-cortex.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **CI/CD Architectural Guard & Ingest Pipeline** — _github_workflows_cortex_detect_workflow, _github_workflows_cortex_ingest_workflow, cortex_vector_mcp_requirements_dependencies [EXTRACTED 1.00]
- **Hackathon Overview, Rules, and Prizes Suite** — hackathon_docs_00_index_index_doc, hackathon_docs_01_overview_overview_doc, hackathon_docs_02_rules_rules_doc, hackathon_docs_03_prizes_prizes_doc [EXTRACTED 1.00]
- **Codebase Cortex ADR System & Invariants** — docs_adr_001_codebase_cortex_adr001, docs_adr_adr_002_distributed_cache_redis_adr002, docs_adr_adr_003_event_driven_architecture_adr003 [EXTRACTED 1.00]
- **Codebase Cortex Architectural Governance & Memory Loop** — skills_cortex_detect_skill_cortex_detect_workflow, skills_cortex_ingest_skill_cortex_ingest_skill, skills_cortex_explain_skill_cortex_explain_skill, skills_cortex_notify_skill_cortex_notify_skill [EXTRACTED 1.00]
- **Qodo Code Quality, Standards & Automated Remediation** — skills_qodo_get_rules_skill_qodo_get_rules_skill, skills_qodo_pr_resolver_skill_qodo_pr_resolver_skill, skills_qodo_pr_resolver_skill_architectural_veto_gate, skills_qodo_pr_resolver_reference_pr_resolver_templates [EXTRACTED 1.00]
- **TrueForge Agent Execution and Runtime Infrastructure** — hackathon_docs_04_trueforge_getting_started_trueforge_harness, hackathon_docs_04_trueforge_getting_started_mcp_tools, hackathon_docs_04_trueforge_getting_started_daytona_sandbox, hackathon_docs_04_trueforge_getting_started_sub_agents [EXTRACTED 1.00]

## Communities (23 total, 11 thin omitted)

### Community 0 - "Vector Indexer & Store"
Cohesion: 0.07
Nodes (36): _bullets(), _extract_paths(), index_directory(), main(), parse_adr_markdown(), Any, Cold-start indexer: parse `docs/adr/ADR-*.md` into the vector store. The ADRs…, Parse one ADR markdown file into an unvalidated payload dict. (+28 more)

### Community 1 - "Architectural Fitness & Rule Enforcement"
Cohesion: 0.06
Nodes (48): dict, Exception, build_parser(), call_matches(), compile_patterns(), dotted_name(), emit(), FitnessError (+40 more)

### Community 2 - "CLI Tooling & Environment Setup"
Cohesion: 0.25
Nodes (20): api(), authHeaders(), die(), doctor(), ensureAgent(), ensureGithubMcp(), ensureSkills(), ensureVectorMcp() (+12 more)

### Community 3 - "Distributed Session Storage"
Cohesion: 0.15
Nodes (19): _client(), create_session(), delete_session(), get_session(), healthcheck(), is_token_revoked(), iter_sessions(), Any (+11 more)

### Community 4 - "Vector MCP Server & API Endpoints"
Cohesion: 0.19
Nodes (19): count(), get_store(), getDecision(), healthcheck(), listDecisions(), Any, Streamable-HTTP MCP server exposing Codebase Cortex vector memory. This is the…, Transition an ADR's status (e.g. ACTIVE -> SUPERSEDED). Preserves every other… (+11 more)

### Community 5 - "Cortex Agent Skills & Workflows"
Cohesion: 0.11
Nodes (20): qodo-get-rules Skill Overview, qodo-pr-resolver Skill Overview, Cortex Detect Architectural Contradiction Analysis, Single-Comment Upsert Strategy, Two-Stage Retrieval and Evaluation Pipeline, Cortex Explain Knowledge Q&A Skill, Multi-Hop ADR Lineage Tracing, Cortex Ingest Knowledge Synchronization Skill (+12 more)

### Community 6 - "Session Storage Fixtures & Demo Modules"
Cohesion: 0.15
Nodes (11): create_session(), get_session(), healthcheck(), iter_sessions(), Any, RuntimeError, In-process session and token-revocation store. Replaces the Redis-backed…, Kept for API compatibility. The in-process store cannot fail this way. (+3 more)

### Community 7 - "Lexical & Vector Search Store"
Cohesion: 0.21
Nodes (6): _LexicalIndex, Any, Store a diff embedding in `diff_embeddings` for drift analytics., Lowercase word tokens, plus path components split on separators.…, Minimal TF-IDF cosine index. Rebuilds on write; the corpus is tiny., _tokenize()

### Community 8 - "Architecture Decision Records & Event Bus"
Cohesion: 0.23
Nodes (13): PR Decision Record Template, cortex-detect Workflow, cortex-ingest Workflow, GitHub Actions Workflows Documentation, Cortex Vector MCP Documentation, Cortex Vector MCP Dependencies, ADR-001: Codebase Cortex Architecture Decision, Two-Stage Contradiction Detection Engine (+5 more)

### Community 9 - "TrueForge Sandbox & Execution Harness"
Cohesion: 0.29
Nodes (7): Daytona Code Execution Sandbox, Model Context Protocol Tools, TrueForge Agent Harness, TrueForge Agent Cookbook, Hackathon Resources and Official Links, Architectural Fitness Verification Checks, Sandbox Patch Verification and Iteration Loop

### Community 10 - "Hackathon Guidelines & Resources"
Cohesion: 0.50
Nodes (4): Hackathon Documentation Index, Hackathon Overview and Core Challenge, Hackathon Rules & Requirements, Hackathon Prize Tracks

### Community 11 - "Demo Scenario Requirements & Fixtures"
Cohesion: 1.00
Nodes (3): Demo Base Requirements, Scenario 1 Ingest Requirements, Scenario 2 Violation Requirements

## Knowledge Gaps
- **24 isolated node(s):** `PR Decision Record Template`, `Cortex Vector MCP Documentation`, `Codebase Cortex Dashboard UI`, `Two-Stage Contradiction Detection Engine`, `Hackathon Overview and Core Challenge` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Store` connect `Vector Indexer & Store` to `Vector MCP Server & API Endpoints`, `Lexical & Vector Search Store`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `_LexicalIndex` connect `Lexical & Vector Search Store` to `Vector Indexer & Store`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Store` (e.g. with `index_directory()` and `ADR`) actually correct?**
  _`Store` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `PR Decision Record Template`, `Cortex Vector MCP Documentation`, `Codebase Cortex Dashboard UI` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Vector Indexer & Store` be split into smaller, more focused modules?**
  _Cohesion score 0.07184325108853411 - nodes in this community are weakly interconnected._
- **Should `Architectural Fitness & Rule Enforcement` be split into smaller, more focused modules?**
  _Cohesion score 0.05878084179970972 - nodes in this community are weakly interconnected._
- **Should `Cortex Agent Skills & Workflows` be split into smaller, more focused modules?**
  _Cohesion score 0.11052631578947368 - nodes in this community are weakly interconnected._