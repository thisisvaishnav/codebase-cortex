# 🏛️ Codebase Cortex — Complete System Architecture

> **A TrueForge-powered agent harness capturing institutional architectural memory, enforcing architectural integrity alongside Qodo in GitHub PRs, and alerting maintainers when foundational architecture is challenged.**

---

## 1. High-Level Architecture Overview

Codebase Cortex bridges developer changes with institutional memory. It monitors PRs and Issues, compares diffs against vector-stored architectural decisions, runs Qodo code reviews, and automatically mentions/escalates to maintainers and original decision authors when foundational architecture is impacted.

```mermaid
flowchart TB
    subgraph GitHub_Ecosystem ["🐙 GitHub Repository & Events"]
        PR_Event["PR Opened / Synchronize"]
        Merge_Event["PR Merged to main"]
        Issue_Event["Issue Opened"]
        CODEOWNERS[".github/CODEOWNERS"]
        PR_Thread["PR / Issue Discussion Thread"]
    end

    subgraph Qodo_Intelligence ["🔍 Qodo Intelligence Layer (Hero #2)"]
        Qodo_Bot["Qodo PR Reviewer (/agentic_review)"]
        Qodo_Rules["Qodo Repo Standards & Rules"]
        Qodo_Resolver["qodo-pr-resolver Skill (Self-Healing)"]
    end

    subgraph CI_Execution ["⚡ GitHub Actions Pipeline"]
        Action_Detect["cortex-detect.yml\n(Headless TF Agent Runner)"]
        Action_Ingest["cortex-ingest.yml\n(Headless TF Agent Runner)"]
    end

    subgraph TrueForge_Harness ["🧠 TrueForge Agent Harness (Hero #1 — Port 8790 / CLI)"]
        TF_Core["agent.json: codebase-cortex"]
        
        subgraph SubAgents ["Dynamic Sub-Agents"]
            Agent_Detect["Detection & Audit Agent"]
            Agent_Ingest["Ingest & Memory Agent"]
            Agent_Notify["Escalation & Router Agent"]
            Agent_Explain["NL Explanation Agent"]
        end

        subgraph Skills_Pack ["Git-Backed Skills (SKILL.md)"]
            Skill_Detect["cortex-detect\n(Two-Stage Evaluator)"]
            Skill_Ingest["cortex-ingest\n(Hybrid Template+Diff Extractor)"]
            Skill_Notify["cortex-notify\n(CODEOWNERS + Author Router)"]
            Skill_Explain["cortex-explain\n(Institutional Q&A)"]
            Skill_QodoRules["qodo-get-rules\n(Fetch Team Standards)"]
            Skill_QodoResolver["qodo-pr-resolver\n(Auto-fix Quality Issues)"]
        end

        subgraph MCP_Layer ["Model Context Protocol (MCP) Connectors"]
            MCP_GH["GitHub MCP\n(PRs, Comments, Issues, Commits)"]
            MCP_VDB["Vector Store MCP\n(ChromaDB / Qdrant)"]
            MCP_FS["Filesystem MCP\n(docs/adr/ Git Sync)"]
        end

        subgraph Sandbox_Layer ["🛡️ Daytona Sandbox"]
            Daytona["Isolated Execution Env\n(AST & Architectural Fitness Tests)"]
        end
    end

    subgraph Knowledge_Base ["💾 Unified Knowledge & Memory Store"]
        Chroma[("Vector DB (ChromaDB)\n- adr_collection (Active/Superseded)\n- diff_embeddings")]
        Git_ADRs[("Git ADR Directory\n/docs/adr/ADR-XXX.md")]
        SQLite_State[("SQLite Session State\n(TrueForge Persistent Context)")]
    end

    subgraph Frontend_App ["🖥️ Web Dashboard (React + Tailwind)"]
        Dash_Timeline["ADR Visual Timeline & Lineage Graph"]
        Dash_Violations["Live Maintainer Violation Feed"]
        Dash_QA["NL Query Interface ('Why did we pick Redis?')"]
        Dash_Drift["Architecture Drift & Deprecation Monitor"]
    end

    %% Event Triggers
    PR_Event --> Qodo_Bot
    PR_Event --> Action_Detect
    Merge_Event --> Action_Ingest
    Issue_Event --> Action_Detect

    %% Action to TrueForge Execution
    Action_Detect --> TF_Core
    Action_Ingest --> TF_Core

    %% Agent Dispatch
    TF_Core --> Agent_Detect
    TF_Core --> Agent_Ingest
    TF_Core --> Agent_Notify
    TF_Core --> Agent_Explain

    %% Detect Flow
    Agent_Detect --> Skill_QodoRules
    Skill_QodoRules -.-> Qodo_Rules
    Agent_Detect --> Skill_Detect
    Skill_Detect --> MCP_VDB
    MCP_VDB <--> Chroma
    Skill_Detect -.-> Daytona
    Skill_Detect --> Agent_Notify
    Agent_Notify --> Skill_Notify
    Skill_Notify --> CODEOWNERS
    Skill_Notify --> MCP_GH
    MCP_GH --> PR_Thread

    %% Ingest Flow
    Agent_Ingest --> Skill_Ingest
    Skill_Ingest --> MCP_FS
    MCP_FS --> Git_ADRs
    Skill_Ingest --> MCP_VDB
    Skill_Ingest --> Agent_Notify

    %% Qodo Flow
    Qodo_Bot --> PR_Thread
    Agent_Detect -.-> Skill_QodoResolver
    Skill_QodoResolver -.-> Qodo_Bot

    %% UI Flow
    Chroma <--> Dash_Timeline
    Chroma <--> Dash_Drift
    SQLite_State <--> Dash_Violations
    Dash_QA --> Agent_Explain
    Agent_Explain --> Skill_Explain
    Skill_Explain --> MCP_VDB
```

---

## 2. Sequence Diagram: Flow 1 — Knowledge Ingestion & Drift Alert on PR Merge

```mermaid
sequenceDiagram
    autonumber
    actor SeniorDev as Senior Developer / Author
    participant GH as GitHub PR (#101)
    participant GHA as GitHub Action (cortex-ingest.yml)
    participant TF as TrueForge Harness (Agent)
    participant SkillIngest as cortex-ingest Skill
    participant SkillNotify as cortex-notify Skill
    participant DB as Vector Database (ChromaDB)
    participant GitDocs as Git ADRs (/docs/adr/)
    actor Maintainer as Repository Maintainer

    SeniorDev->>GH: Fill PR Decision Template & Merge to main
    GH->>GHA: webhook: pull_request.closed (merged=true)
    GHA->>TF: Run TrueForge Ingest Agent (pr_metadata, diff, author)
    TF->>SkillIngest: Execute cortex-ingest
    
    alt PR contains Decision Template
        SkillIngest->>SkillIngest: Parse structured markdown fields
    else Fallback Automated Extraction
        SkillIngest->>SkillIngest: LLM extracts Architectural Invariants from diff
    end

    SkillIngest->>GitDocs: Write docs/adr/ADR-004-new-decision.md
    SkillIngest->>DB: Store record (id, author, reasoning, files, status=ACTIVE)
    DB-->>TF: Confirmed indexed

    alt Overrides Prior ADR
        TF->>DB: Update prior ADR status to SUPERSEDED (pointer: PR #101)
        TF->>SkillNotify: Run cortex-notify (Fetch prior ADR author & CODEOWNERS)
        SkillNotify->>GH: Post Drift Notice tagging @Maintainer & @SeniorDev
        GH-->>Maintainer: GitHub Notification: Architecture Drift Notice
    else Normal Decision Ingest
        TF->>GH: Post confirmation comment (Indexed into Cortex memory — ADR-00X created)
    end
```

---

## 3. Sequence Diagram: Flow 2 — PR Contradiction Detection & Maintainer Alert

```mermaid
sequenceDiagram
    autonumber
    actor NewDev as New Developer
    participant GH as GitHub PR (#102)
    participant Qodo as Qodo PR Agent
    participant GHA as GitHub Action (cortex-detect.yml)
    participant TF as TrueForge Harness (Agent)
    participant SkillQodoRules as qodo-get-rules Skill
    participant SkillDetect as cortex-detect Skill
    participant SkillNotify as cortex-notify Skill
    participant DB as Vector Database (Memory)
    participant Sandbox as Daytona Sandbox
    actor SeniorDev as Original Decision Author / Maintainer

    NewDev->>GH: Open / Update PR (e.g. replaces Redis with In-Memory Cache)

    par Parallel Track 1: Qodo Code Quality Review
        GH->>Qodo: PR Created / Synchronize Webhook
        Qodo->>Qodo: Context-aware Code Review & Analysis
        Qodo->>GH: Post Code Quality & Security Findings
        Note over Qodo,GH: Severity: ERROR / WARNING / RECOMMENDATION
    and Parallel Track 2: Codebase Cortex Architectural Audit
        GH->>GHA: PR Created / Synchronize Webhook
        GHA->>TF: Run TrueForge Detect Agent (diff, files_changed, pr_id)
        TF->>SkillQodoRules: Fetch repo coding standards first
        SkillQodoRules-->>TF: Standards loaded into agent context
        
        TF->>SkillDetect: Execute Two-Stage Detection Engine
        Note over SkillDetect,DB: Stage 1: Dense Semantic Retrieval
        SkillDetect->>DB: Query nearest semantic decisions for affected files
        DB-->>SkillDetect: Return ADR-003 (Redis chosen by @senior-dev, cosine sim: 0.91)
        
        Note over SkillDetect: Stage 2: Intent & Invariant Verification
        SkillDetect->>SkillDetect: Verify if diff violates pod-restart persistence invariant
        
        opt Validation Script Needed
            SkillDetect->>Sandbox: Execute AST import / fitness check in Daytona
            Sandbox-->>SkillDetect: Validation pass/fail
        end

        alt Violation Confirmed (Confidence >= 80%)
            SkillDetect->>SkillNotify: Resolve CODEOWNERS & @senior-dev
            SkillNotify->>GH: Upsert Single Warning Comment (<!-- codebase-cortex:pr-analysis -->)
            Note over SkillNotify,GH: Architectural Conflict Detected — CC @senior-dev @repo-maintainers
            GH-->>SeniorDev: Push Notification: Tagged in Architectural Review
        else No Violation / Compliant
            SkillDetect->>GH: Upsert Clean Architectural Audit status
        end
    end

    Note over TF: Developer remediation loop
    opt Self-healing Qodo Fixes
        TF->>SkillDetect: Invoke qodo-pr-resolver
        SkillDetect->>GH: Reply to inline review threads & push fixes
    end
```

---

## 4. Sequence Diagram: Flow 3 — Pre-flight Issue Scanning

```mermaid
sequenceDiagram
    autonumber
    actor Contributor as Contributor
    participant GH as GitHub Issue (#88)
    participant GHA as GitHub Action (cortex-detect.yml)
    participant TF as TrueForge Harness (Agent)
    participant DB as Vector Database (Memory)
    actor Maintainer as Maintainer

    Contributor->>GH: Open Issue: "Proposing to swap Redis with Local Storage"
    GH->>GHA: webhook: issues.opened
    GHA->>TF: Run TrueForge Scan Issue (title, body, issue_number)
    TF->>DB: Semantic query against historical ADRs
    DB-->>TF: Matches ADR-003 (Redis justification, similarity: 0.87)
    TF->>GH: Post Issue Comment via GitHub MCP
    Note over TF,GH: Heads up — ADR-003 by @senior-dev decided on Redis for pod resilience. CC: @Maintainer
    GH-->>Maintainer: Notified before PR is written
```

---

## 5. Sequence Diagram: Flow 4 — Natural Language Query via Dashboard

```mermaid
sequenceDiagram
    autonumber
    actor User as Developer / Tech Lead
    participant Dash as Web Dashboard (React/Vite)
    participant TF as TrueForge Harness (Agent)
    participant AgentExplain as Explain Sub-Agent
    participant SkillExplain as cortex-explain Skill
    participant DB as Vector Database (Memory)

    User->>Dash: "Why did we choose Redis over Postgres?"
    Dash->>TF: Run Explain Sub-Agent with question
    TF->>AgentExplain: Spin up Explain Sub-Agent
    AgentExplain->>SkillExplain: Execute cortex-explain with user question
    SkillExplain->>DB: Semantic search over all indexed ADRs
    DB-->>SkillExplain: Return ADR-003, ADR-007 (related decisions)
    SkillExplain-->>AgentExplain: Compose structured explanation with decision lineage
    AgentExplain-->>TF: Response with ADR references & original author attributions
    TF-->>Dash: Return structured answer with lineage
    Dash-->>User: Redis was chosen (ADR-003, @senior-dev, 3 months ago) because Postgres was too slow under 10k concurrent sessions. ADR-003 is still ACTIVE.
```

---

## 6. TrueForge Harness Configuration (`agent.json` Architecture)

```mermaid
classDiagram
    class TrueForgeAgent {
        +String name: "codebase-cortex"
        +String model: "gpt-4o / gemini-2.5-pro"
        +String instructions
        +List connectors
        +List skills
        +List subAgents
        +executeWorkflow()
        +persistState()
    }

    class MCPConnectors {
        +GitHub_MCP: readDiff(), postComment(), upsertComment(), mentionUsers(), readIssue(), readCODEOWNERS()
        +VectorStore_MCP: searchDecisions(), upsertDecision(), updateStatus(), markSuperseded()
        +Filesystem_MCP: readADR(), writeADR(), listADRs()
    }

    class SkillsPack {
        +cortex_detect: evaluateContradictionTwoStage(diff, standards, adrs)
        +cortex_ingest: parseAndStorePRTemplate(pr, author, files)
        +cortex_notify: resolveMaintainersAndTag(adr, violation)
        +cortex_explain: answerNLQuery(question)
        +qodo_get_rules: fetchRepositoryRules()
        +qodo_pr_resolver: autoResolveReviewComments()
    }

    class MemorySystem {
        +SQLiteState: Persistent agent state across sessions
        +VectorIndex: Architectural decisions semantic space
        +ADR_Status: ACTIVE | SUPERSEDED | DEPRECATED
    }

    class DaytonaSandbox {
        +executeCode(script): SafeIsolation
        +validateFitnessFunction(): BooleanResult
    }

    TrueForgeAgent --> MCPConnectors : delegates tool calls
    TrueForgeAgent --> SkillsPack : follows procedural instructions
    TrueForgeAgent --> MemorySystem : stores & retrieves context
    TrueForgeAgent --> DaytonaSandbox : sandboxed code execution
```

---

## 7. Execution Modes: CI Runner vs. Local Daemon

Codebase Cortex supports two execution topologies:

1. **Headless CI Runner Mode (GitHub Actions):**
   - Workflow executes `npx @truefoundry/trueforge run agent.json --input "..."`.
   - Runs deterministically in the ephemeral GitHub runner.
   - Accesses repo secrets (`TF_API_KEY`, `GITHUB_TOKEN`).
   - Idempotent and zero-server dependency.

2. **Interactive Daemon Mode (Local / Dashboard):**
   - TrueForge server runs on `http://localhost:8790`.
   - Web Dashboard communicates via REST / SSE streaming.
   - Perfect for live interactive queries and visual exploration during development and live demos.

---

## 8. Two-Stage Detection Engine & Confidence Calibration

| Stage | Mechanism | Purpose |
|---|---|---|
| **Stage 1: Retrieval** | Dense Bi-Encoder Embedding Search (Cosine Similarity $\ge 0.70$) | Retrieve top-5 candidate ADRs whose scope intersects modified files and concepts. |
| **Stage 2: Intent Evaluation** | LLM Cross-Encoder Evaluation via `cortex-detect` skill | Analyze semantic intent: does the diff break the invariant or simply refactor cleanly? |

### Confidence & Action Matrix

| Score Range | Classification | Action |
|---|---|---|
| **High ($\ge 80\%$)** | **Hard Violation** | Post violation comment + escalate to original author & CODEOWNERS |
| **Medium ($60\% - 79\%$)** | **Advisory Notice** | Post advisory note: "Possible architectural intersection, verify ADR alignment" |
| **Low ($< 60\%$)** | **Compliant / Orthogonal** | Silent pass or green audit badge |

---

## 9. Technology Stack & Role Matrix

| Layer | Component | Choice | Reason & Superpower |
|---|---|---|---|
| **Runtime Harness** | Agent OS | **TrueForge** (`@truefoundry/trueforge`) | Complete harness with MCP, persistent SQLite memory, subagents & skills |
| **Code Intelligence** | Code Review & Standards | **Qodo** | Repo-wide semantic comprehension, `qodo-get-rules` & `qodo-pr-resolver` skills |
| **Automation** | Event Triggers | **GitHub Actions** | Zero-latency event pipeline for `pull_request` & `issues` |
| **Maintainer Routing** | Notification Engine | `cortex-notify` Skill | Tags original decision author and CODEOWNERS on violation/drift with deduplication |
| **Memory / RAG** | Vector Database | **ChromaDB / Qdrant** | High-speed semantic similarity matching over code & reasoning |
| **Session State** | Persistent State | **SQLite** (TrueForge built-in) | Agent carries context across sessions without external infra |
| **Sandboxing** | Code Execution | **Daytona** | Safe isolated environment for optional AST/fitness validation scripts |
| **Integrations** | Protocols | **Model Context Protocol (MCP)** | Native, standard tool invocation for GitHub, Storage & Filesystem |
| **NL Query** | Explanation Engine | `cortex-explain` Skill | Answers "Why did we do X?" against indexed ADR memory |
| **Dashboard** | Frontend UI | **React + Tailwind CSS** | Real-time decision timeline, SUPERSEDED lineage graph, NL search, demo console |

---

## 10. Skills Summary

| Skill | File | Purpose |
|---|---|---|
| `cortex-detect` | `skills/cortex-detect/SKILL.md` | Two-stage diff and issue contradiction detection (Retrieval + LLM Intent Evaluator) |
| `cortex-ingest` | `skills/cortex-ingest/SKILL.md` | Hybrid template & diff extraction, indexing, and git ADR sync |
| `cortex-notify` | `skills/cortex-notify/SKILL.md` | CODEOWNERS resolution, maintainer tagging, and comment deduplication |
| `cortex-explain` | `skills/cortex-explain/SKILL.md` | Natural language explanation of institutional decisions |
| `qodo-get-rules` | `skills/qodo-get-rules/SKILL.md` | Fetches repo standards before analysis (runs first in detect flow) |
| `qodo-pr-resolver` | `skills/qodo-pr-resolver/SKILL.md` | Self-healing loop: resolves Qodo findings, posts commits, replies to inline threads |
