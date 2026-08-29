---
name: cortex-detect
description: Analyzes git diffs and issue proposals to detect contradictions against institutional architectural decision records (ADRs).
---

# Cortex Detect Skill

## Overview
This skill performs two-stage architectural contradiction analysis on an incoming PR diff or Issue proposal against the repository's indexed architectural memory. It is invoked as `cortex detect --pr <n>` (`pull_request.opened|synchronize|reopened`) or `cortex detect --issue <n>` (`issues.opened`).

Tools: the remote **`github`** MCP for diffs, issues and comments (plausible tool names `get_pull_request`, `get_pull_request_diff`, `get_issue`, `list_issue_comments`, `add_issue_comment`, `update_issue_comment`, `get_file_contents`; confirm against the live tool list), the remote **`cortex-vector`** MCP for retrieval (`searchDecisions`, `upsertDecision`, `updateStatus`), and your **sandbox** for running fitness checks. Never assert a violation from the diff alone — retrieve first.

## Workflow

### 1. Pre-computation & Standards Fetch
- Always invoke `qodo-get-rules` first, so repository coding standards are in context before you judge anything. A change that Qodo's rules already sanction is not architectural drift.
- **PR path:** read the diff via the `github` MCP. Extract changed file paths, added/removed dependencies, modified function and class symbols, and a 2-3 sentence semantic summary of what the diff *intends*.
- **Issue path (pre-flight):** read the issue title and body. There is no diff — build the query from the proposal text and any file paths, modules or technologies it names. Everything below applies, except the fitness checks (step 4), which are skipped.

### 2. Stage 1: Dense Retrieval
- Call `searchDecisions(query=<diff or proposal summary>, paths=<changed paths>, threshold=0.70, include_superseded=false)`.
- Keep only records whose `status == ACTIVE`. A SUPERSEDED ADR describes history, not a live constraint — never escalate against one (mention it only as context if it is an ancestor of an active record).
- Take the **top 5** candidates by cosine similarity. If none clear `0.70`, there is nothing to reason about: classify `COMPLIANT` and stop after posting the clean-audit badge.
- Retrieval score is a *routing* signal only. It never becomes the confidence in step 3.

### 3. Stage 2: Invariant & Intent Evaluation (Cross-Encoder Reasoning)
For each retrieved candidate ADR:
1. Read its `invariants` field — the explicit MUST / MUST NEVER rule (e.g. "Session state MUST NOT be stored in process memory", "Billing side-effects MUST be emitted as events and processed asynchronously").
2. Compare the change's *intent* against that rule, not its surface tokens. Renaming, extracting or relocating code that still satisfies the invariant is a clean refactor. Ask concretely: after this change, is the invariant still true at runtime?
3. Classify into exactly one state:
   - `HARD_VIOLATION` — the change directly reverses or breaks a foundational decision, and no ADR update accompanies it.
   - `ARCHITECTURAL_DRIFT` — the change partially shifts the architecture, or introduces a competing mechanism alongside the sanctioned one, without maintainer sign-off.
   - `ADVISORY` — the change touches an architectural boundary but adheres to the pattern; worth a note, not an escalation.
   - `COMPLIANT` — no contradiction.
4. Score confidence on the *reasoning*, and calibrate honestly:

| Confidence | Classification band | Action |
|---|---|---|
| `>= 0.80` | `HARD_VIOLATION` / `ARCHITECTURAL_DRIFT` | Escalate: hand off to `cortex-notify` to page the ADR author and CODEOWNERS |
| `0.60 – 0.79` | `ADVISORY` | Upsert an advisory note. No mentions, no paging |
| `< 0.60` | `COMPLIANT` | Silent pass. Upsert the clean-audit badge only |

Never inflate a score to make a finding actionable, and never escalate without naming the specific invariant sentence that breaks.

### 4. Architectural Fitness Checks (sandbox)
Before escalating a PR-path finding, verify it mechanically in the sandbox (Daytona when configured, local fallback otherwise). Write and run a short python script — never execute repository code, only parse it:
- **Import-boundary check:** walk the changed files with python's `ast` module, collect `Import` / `ImportFrom` nodes, and assert the layering the ADR requires (e.g. nothing under `src/core/` may import from `src/api/`; a module in the ADR's scope must still import the sanctioned client).
- **Banned-dependency check:** diff the dependency manifests and grep imports for technologies the ADR rules out (e.g. an in-process cache library appearing where the ADR mandates Redis).

Each check yields `pass`, `fail`, or `skipped` (with a reason — missing file, unparsable, no checkout in the sandbox). A `fail` is corroborating evidence and raises confidence; `skipped` never lowers it below the band the reasoning earned. Report the checks even when they pass — they are the difference between an assertion and a demonstration.

### 5. Output Contract
Return a JSON object:
```json
{
  "has_violation": true,
  "confidence": 0.92,
  "classification": "HARD_VIOLATION",
  "violated_adr_id": "ADR-002",
  "violated_adr_title": "Redis for Distributed Session Persistence",
  "author": "senior-dev",
  "reason": "PR replaces Redis session storage with an in-process dict in src/cache/session.py, so session state is lost on pod restart — this reverses the ADR-002 invariant.",
  "affected_files": ["src/cache/session.py"],
  "fitness_checks": [
    { "name": "banned-dependency", "status": "fail", "detail": "src/cache/session.py no longer imports the redis client; a module-level dict now holds session state." },
    { "name": "import-boundary", "status": "pass", "detail": "No src/core -> src/api imports introduced." }
  ]
}
```
`classification` is one of `HARD_VIOLATION`, `ARCHITECTURAL_DRIFT`, `ADVISORY`, `COMPLIANT`. When `COMPLIANT`, set `has_violation: false` and leave the ADR fields `null`. For the issue path, `affected_files` holds the paths or modules the proposal names and `fitness_checks` is `[]`.

### 6. Single-Comment Upsert
Every verdict — violation, advisory or clean — results in **one** comment carrying the marker `<!-- codebase-cortex:pr-analysis -->`. List the thread's comments via the `github` MCP, find the one containing the marker, and **update** it; only create a comment when no marker exists. Never add a second one, on a PR or an issue.

`cortex-notify` owns the write: hand it this JSON verdict plus the PR/issue number and author, and let it resolve mentions, format the body, and apply its dedup and cooldown rules. Do not post directly from this skill.
