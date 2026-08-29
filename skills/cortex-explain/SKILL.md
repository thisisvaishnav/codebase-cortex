---
name: cortex-explain
description: Answers natural language questions about historical architectural decisions, trade-offs, and design lineage.
---

# Cortex Explain Skill

## Overview
This skill is the conversational Q&A interface for institutional knowledge, answering developer questions like *"Why did we choose Redis?"* or *"What is our policy on distributed locking?"*. It reads memory and never writes to it — no `upsertDecision`, no `updateStatus`, no comments.

Tools: the remote **`cortex-vector`** MCP (`searchDecisions`) and, when the answer needs prose the vector record does not carry, the remote **`github`** MCP to read the ADR file itself (plausible tool name `get_file_contents`; confirm against the live tool list).

## Workflow

### 1. Intent Extraction & Search
- Distil the question into a retrieval query: the technologies, components and paths it names, plus the decision being asked about.
- Call `searchDecisions(query=<question>, paths=<any paths or modules named, else omitted>, threshold=0.60, include_superseded=true)`.
  - **`include_superseded=true` is required here.** Q&A is the one path that must see history — "why did we choose Redis" is often answered by a record that has since been retired.
  - Threshold is lowered from the `0.70` detection default: recall matters more than precision when a human is reading the answer.
- The search is hybrid — dense similarity over `title`, `invariants`, `reasoning` and `alternatives_rejected`, plus keyword matching on technology and component names. If a distinctive term in the question (a library, a service) appears in no record, say so rather than answering from the nearest neighbour.

### 2. Multi-Hop Lineage Tracing
A single ADR is rarely the whole answer. From each match, walk the chain in **both** directions until it terminates:
- **Forward:** follow `superseded_by_adr` to the record that replaced it, then follow that record's `superseded_by_adr`, and so on, until you reach a record whose `status` is `ACTIVE`. Note each hop's `superseded_by_pr` — that PR is where the change was argued.
- **Backward:** find the ancestor by looking for the record whose `superseded_by_adr` equals the current id, or by reading the `**Supersedes:** ADR-XXX` line from the ADR file. Repeat to the original decision.
- Order the chain oldest → newest and answer from the **whole** chain: the current rule is the tip, but the reasoning that produced it usually lives further back.
- Guard the walk: cap it at 10 hops and track visited ids, so a mis-recorded cycle cannot loop.

### 3. Response Format
Answer in prose, then attribute. Every claim traces to a record:

```markdown
**Current answer:** <the rule in force today, one or two sentences.>

- **Decision:** ADR-002 — Redis Cluster for session persistence
- **Rationale:** <the specific technical reasoning and any benchmark or incident cited>
- **Alternatives rejected:** <each one, with why it lost>
- **Author:** @senior-dev · **Date:** 2026-05-15 · **Status:** ACTIVE
- **Lineage:** ADR-002 (ACTIVE) — no prior decision superseded

**Invariant still in force:** <the MUST / MUST NEVER sentence.>
```

When the tip of the chain is superseded, state the reversal plainly and keep both sides: *"ADR-002 chose Redis (@senior-dev, 2026-05-15); it was superseded by ADR-005 in PR #134 (@lead-maintainer), which moved sessions to signed cookies because …"* — give status and superseding PR for every hop.

**Never invent an ADR.** Cite ids, authors and dates exactly as stored. If retrieval returns nothing above threshold, say the decision is not recorded in Cortex memory and suggest the question be captured as an ADR via the PR decision template — do not reason a plausible-sounding rationale into existence.

## Query Surfaces
This skill is exposed two ways, both driving the same agent through the TrueForge REST API (`POST /sessions`, `POST /sessions/{id}/turns`):
- **CLI:** `bin/cortex explain --question "Why did we choose Redis over Postgres?"` — the answer goes to stdout, so it pipes in CI and demos.
- **Dashboard:** the natural-language console, which streams the turn over SSE (`GET /sessions/{id}/turns/{turn_id}/subscribe`) and renders the lineage chain from step 2 as a graph.

Keep answers self-contained enough to read in either surface: no references to earlier turns, and no markdown that depends on GitHub-only rendering.
