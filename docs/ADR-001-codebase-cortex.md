# ADR-001: Codebase Cortex — Architecture Decision Record

**Status:** Accepted  
**Date:** 2026-08-29  
**Hackathon:** The Agent Harness Hackathon — WeMakeDevs × TrueFoundry  
**Deadline:** August 30, 2026 at 8:00 PM London time  

---

## The Problem

AI tools tell you **what** code does. Nobody tells you **why** it was written that way.

When a senior developer leaves or steps away, the institutional knowledge — the reasoning behind foundational architectural decisions — leaves with them. The next developer changes a line or merges a fix, not knowing it breaks or contradicts a rule that was set 6 months ago for a critical reason (e.g., resilience, scaling, compliance). Furthermore, **maintainers and leads are often left out of the loop** when subtle foundational changes slip through pull requests or issues.

**Codebase Cortex** fixes this.

---

## The One-Line Pitch

> A TrueForge agent that catches architectural violations in PRs & issues, preserves institutional memory, and proactively alerts maintainers when foundational architecture is touched or altered.

---

## The Demo Moments (Everything is designed around this)

### Demo Moment 1: PR Violation & Maintainer Alert
1. Senior dev merges a foundational decision: *"Why Redis? Because Postgres was too slow under 10k concurrent sessions — we benchmarked this."*
2. Codebase Cortex ingests this decision into its memory with `@senior-dev` recorded as the author/maintainer.
3. Three months later, a new developer opens a PR replacing Redis with an in-memory cache.
4. **Two comments appear on the PR within 60 seconds:**
   - **Qodo:** Code quality, security, and repository standards review.
   - **Codebase Cortex (TrueForge agent):** *"⚠️ Architectural Conflict Detected: This contradicts ADR-003 by @senior-dev. In-memory caching loses session data on pod restart. Pinging @repo-maintainers @senior-dev for architectural review."*

### Demo Moment 2: Issue Pre-flight & Merge Drift Alert
1. A contributor opens an Issue proposing to remove Redis. Cortex automatically scans the proposal, references ADR-003, and notifies the maintainers before code is written.
2. If a PR intentionally changes or supersedes an ADR upon merge, Cortex triggers a **Maintainer Drift Alert** tagging `@repo-maintainers` to confirm the architectural evolution.

---

## Why TrueForge is Non-Removable (Hero #1)

TrueForge is the **agent harness** — the runtime that turns the LLM into a working agent.

| Without TrueForge | With TrueForge |
|---|---|
| Rigid, brittle custom scripts | Intelligent agent harness with MCP tools, skills, dynamic sub-agents, and persistent SQLite memory |
| Manual context & prompt stuffing | Persistent session state carrying architectural context across runs |
| Hardcoded GitHub API calls | Native GitHub MCP connector for PRs, issues, diffs, and CODEOWNERS mentions |
| Rebuilding tool integrations from scratch | Git-backed portable Skills (`SKILL.md`) following the Agent Skills standard |
| Unsafe local code execution | Daytona sandbox integration for isolated AST & architectural fitness checks |

**The agent cannot exist without TrueForge. It is the skeleton.**

---

## Why Qodo is Non-Removable (Hero #2)

Qodo is the **code intelligence layer** that understands the full repository context — not just the diff.

| Without Qodo | With Qodo |
|---|---|
| Manual diff parsing in isolation | Whole-repo context, dependencies, history, and standards enforcement |
| Generic or unranked bot comments | Severity-ranked quality, bug, and security findings (`/agentic_review`) |
| Fragmented developer experience | Unified PR review: code quality (Qodo) + architectural integrity (Cortex) |
| Ignorant of repository standards | `qodo-get-rules` skill loads repo standards directly into Cortex context before scanning |
| Manual remediation overhead | `qodo-pr-resolver` skill enables self-healing review resolution loops |

**Qodo is the eyes. TrueForge is the brain. Neither works alone.**

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GITHUB REPOSITORY                             │
│                                                                         │
│   Issue Opened ─────────────────────────────────────────────────────┐   │
│   PR Opened / Updated ──────────────────────────────────┐           │   │
│   PR Merged ──────────────────────────────────────┐     │           │   │
└───────────────────────────────────────────────────┼─────┼───────────┼───┘
                                                    │     │           │
              ┌─────────────────────────────────────┤     │           │
              │                                     ▼     ▼           ▼
              │                          ┌────────────────────────────────┐
              │                          │         GITHUB ACTIONS         │
              │                          │ • cortex-detect.yml (PR/Issue) │
              │                          │ • cortex-ingest.yml (Merge)    │
              │                          └───────────────┬────────────────┘
              ▼                                          │
   ┌────────────────────┐                                │
   │    QODO AGENT      │                                │
   │                    │                                │
   │  Auto-reviews PR   │                                │
   │  Code quality +    │                                │
   │  standards check   │                                │
   │                    │                                │
   │  /agentic_review   │                                │
   └──────────┬─────────┘                                │
              │                                          ▼
              │         ┌────────────────────────────────────────────────────────┐
              │         │        TRUEFORGE — The Agent Runtime (HERO #1)         │
              │         │                                                        │
              │         │  agent.json: codebase-cortex                           │
              │         │                                                        │
              │         │  MCP Connectors:                                       │
              │         │  ├── GitHub MCP      → PRs, Issues, @Maintainers       │
              │         │  ├── Vector Store MCP→ Store & Semantic Query ADRs     │
              │         │  └── Filesystem MCP  → Git-backed /docs/adr/ sync      │
              │         │                                                        │
              │         │  Skills (SKILL.md):                                    │
              │         │  ├── cortex-detect   → 2-Stage Contradiction Engine    │
              │         │  ├── cortex-ingest   → Hybrid Template + Diff Extractor│
              │         │  ├── cortex-notify   → CODEOWNERS & Author Router      │
              │         │  ├── cortex-explain  → Natural Language ADR Q&A Engine │
              │         │  ├── qodo-get-rules  → Fetch repo coding standards     │
              │         │  └── qodo-pr-resolver→ Auto-fix Qodo findings          │
              │         │                                                        │
              │         │  Dynamic Sub-agents:                                   │
              │         │  ├── Detect Agent    → Scans PRs/Issues for conflicts  │
              │         │  ├── Ingest Agent    → Processes merged PR decisions   │
              │         │  ├── Notify Agent    → Resolves CODEOWNERS & alerts    │
              │         │  └── Explain Agent   → Answers "Why was X chosen?"    │
              │         └───────────────────────────────┬────────────────────────┘
              │                                         │
              ▼                                         ▼
   ┌─────────────────────────────────────────────────────────────────────────────┐
   │                            GITHUB PR / ISSUE THREAD                         │
   │                                                                             │
   │  [Qodo]: Code Quality, Linter, Security Findings                            │
   │  [Codebase Cortex]: ⚠️ Architectural Conflict Detected                       │
   │                     "Contradicts ADR-003 by @senior-dev."                   │
   │                     "CC: @lead-maintainer @senior-dev"                      │
   └─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Operational Flows

### Flow 1: Knowledge Ingestion & Maintainer Record (PR Merged)

1. **Trigger:** PR merged to `main` (`pull_request.closed` with `merged == true`).
2. **Action:** GitHub Action `cortex-ingest.yml` invokes TrueForge Ingest Agent.
3. **Execution:** TrueForge runs `cortex-ingest` skill:
   - Parses the PR Decision Template if present.
   - Falls back to automated LLM extraction if significant architectural files changed.
   - Writes/updates the git-backed markdown file under `docs/adr/`.
   - Embeds and indexes the decision metadata into ChromaDB vector store (`status=ACTIVE`).
4. **Drift Alert:** If this PR supersedes or modifies a prior ADR, TrueForge triggers `cortex-notify` to tag original decision authors and repository maintainers (`.github/CODEOWNERS`) in a merge summary comment.

### Flow 2: Contradiction Detection & Maintainer Escalation (PR Opened)

1. **Trigger:** PR opened or updated (`pull_request.opened`, `pull_request.synchronize`).
2. **Dual Review:**
   - **Qodo** initiates repository-wide code quality, security, and standards review (`/agentic_review`).
   - **TrueForge** runs `cortex-detect.yml` to extract diff and invoke the Detection Agent.
3. **Two-Stage Violation Check:**
   - **Stage 1 (Dense Retrieval):** Query Vector Store for top-5 semantically relevant ADRs based on changed file paths, modified symbols, and diff summary.
   - **Stage 2 (Intent Classification):** LLM evaluates candidate ADRs against diff intent to distinguish valid refactors from genuine invariant violations.
4. **Escalation & Deduplication:** If a contradiction is detected (confidence $\ge 80\%$):
   - Formulates violation explanation with original reasoning and ADR reference.
   - Retrieves the original author and repository maintainers (`.github/CODEOWNERS`).
   - Upserts a single comment on GitHub using a deterministic identifier marker (`<!-- codebase-cortex:pr-analysis -->`) mentioning `@senior-dev` and `@repo-maintainers`.

### Flow 3: Pre-flight Issue Scanning (Issue Opened)

1. **Trigger:** Issue opened proposing a refactor or architectural change (`issues.opened`).
2. **Action:** TrueForge scans the issue description against architectural memory in ChromaDB.
3. **Execution:** Posts historical context as an issue comment: *"Before starting: ADR-003 outlines why Redis was chosen over in-memory. Pinging @senior-dev."*

### Flow 4: Natural Language ADR Querying (Dashboard / Chat)

1. **Trigger:** Developer asks *"Why did we choose Redis over Postgres?"* in the Web Dashboard.
2. **Action:** TrueForge runs `cortex-explain` sub-agent against ChromaDB ADR memory.
3. **Execution:** Synthesizes historical context, benchmark citations, and lineage (e.g. Active vs. Superseded status) in plain English.

---

## PR Decision Template

```markdown
## 🧠 Codebase Cortex — Decision Record

### What changed?
<!-- Brief summary of the technical change -->

### Why this decision?
<!-- The reasoning. Why this approach over alternatives? -->

### Alternatives rejected
<!-- What else was considered and why it was ruled out -->

### Affected files / modules
<!-- Auto-detected from diff, override if needed -->

### Architectural Decision?
- [ ] Yes — foundational change (Capture in Cortex & notify maintainers)
- [ ] No — standard fix/feature following existing patterns
```

---

## Violation Comment Format (With Maintainer Mention)

```markdown
<!-- codebase-cortex:pr-analysis -->
⚠️ **Codebase Cortex — Architectural Conflict Detected**

This change appears to contradict a foundational architectural decision.

- **Violated Decision:** [ADR-003: Redis for Distributed Session Persistence](docs/adr/ADR-003-distributed-cache-redis.md)
- **Original Reasoning (by @senior-dev · 3 months ago):** Redis was selected over in-memory caching because the service must survive Kubernetes pod restarts without session loss.
- **Confidence Score:** 91% (Hard Violation)
- **Files Affected:** `src/cache/session.py`

🔔 **Maintainer Escalation:** Paging @senior-dev and @repo-maintainers for architectural review.

*If this change is intentional, please update the decision record in this PR's description and tick the architectural decision checkbox.*

— *Powered by Codebase Cortex + TrueForge + Qodo*
```

---

## Skills to Build

| Skill | File | Purpose |
|---|---|---|
| `cortex-detect` | `skills/cortex-detect/SKILL.md` | Two-stage diff and issue contradiction detection |
| `cortex-ingest` | `skills/cortex-ingest/SKILL.md` | Hybrid template & diff extraction, indexing, and git ADR sync |
| `cortex-notify` | `skills/cortex-notify/SKILL.md` | CODEOWNERS resolution, maintainer tagging, and comment deduplication |
| `cortex-explain` | `skills/cortex-explain/SKILL.md` | Natural language explanation of institutional decisions |
| `qodo-get-rules` | `skills/qodo-get-rules/SKILL.md` | Fetches repo standards before analysis |
| `qodo-pr-resolver` | `skills/qodo-pr-resolver/SKILL.md` | Resolves Qodo findings in development self-healing cycle |

---

## Judging Track Alignment

| Track | Alignment |
|---|---|
| **Best Use of TrueForge** | Core runtime engine coordinating MCP tools (GitHub, Vector Store, Filesystem), skills (`cortex-detect`, `cortex-notify`, `cortex-ingest`, `cortex-explain`), dynamic sub-agents, and persistent SQLite memory. |
| **Best Code Quality** | Deep Qodo integration: reviews every PR, adheres to Qodo repo rules, and demonstrates self-healing with `qodo-pr-resolver`. |
| **Best UI** | Visual dashboard displaying real-time decision graph, violation feed, maintainer audit trail, and natural language search. |
