---
name: cortex-ingest
description: Extracts, formats, and indexes architectural decisions upon PR merge, synchronizing git ADR files and vector memory.
---

# Cortex Ingest Skill

## Overview
This skill runs after a PR merges (`pull_request.closed` with `merged == true`), invoked as `cortex ingest --pr <n> [--author <login>]`. It captures institutional knowledge into two places that must agree: git-tracked Markdown under `docs/adr/`, and the `cortex-vector` MCP server's semantic memory.

Tools: the remote **`github`** MCP for PR body, diff, comments and file contents (plausible tool names `get_pull_request`, `get_pull_request_diff`, `get_file_contents`, `list_issue_comments`, `add_issue_comment`, `update_issue_comment`, `create_or_update_file`; confirm against the live tool list), the remote **`cortex-vector`** MCP (`searchDecisions`, `upsertDecision`, `updateStatus`), and your **sandbox** shell/python. There is no filesystem MCP — every file read, write and text transform happens in the sandbox.

## Ingestion Workflow

### 1. Hybrid Extraction
Read the merged PR body and diff via the `github` MCP.

- **Path A (Template Parsing):** If the body contains the heading `## 🧠 Codebase Cortex — Decision Record`, parse these `###` sections from `.github/pull_request_template.md`:
  - `What changed?` → the decision statement
  - `Why this decision?` → rationale
  - `Alternatives rejected` → alternatives
  - `Affected files / modules` → scope (union with the diff's real paths; the diff wins on conflict)
  - `Architectural Decision?` → the two checkboxes. `- [x] Yes` means ingest. `- [x] No`, or neither ticked with placeholder comments left intact, means **stop** — post nothing, create no ADR.
  - Treat a section whose only content is its `<!-- … -->` hint as empty.
- **Path B (Fallback LLM extraction):** If the template is absent or unparsed, check whether the diff touches architectural surface: `src/core/**`, `src/cache/**`, `config/**`, `infra/**`, `migrations/**`, CI workflows, container/compose files, or a dependency manifest (`package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`) where a dependency was added or removed. If none of those changed, stop — a normal feature or fix is not an ADR. If they did, read the diff plus the PR title, description and review discussion, and extract the same five fields yourself. State in the ADR that it was auto-extracted.
- **Supersede signal:** look for `supersedes: ADR-00N` (body or template text), or a diff that removes/inverts the invariant of a known ADR. Confirm the target with `searchDecisions` before acting.

### 2. Sequential ID and Slug
In the sandbox, list every `ADR-*.md` under both `docs/` and `docs/adr/`, take the highest number, add one, and zero-pad to three digits. Existing records are **ADR-001** (`docs/ADR-001-codebase-cortex.md` — the project design record, kept at `docs/` for history), **ADR-002** and **ADR-003** (`docs/adr/`), so the next id is **ADR-004**. Numbering is global across both directories; new files always land in `docs/adr/`.

When the sandbox does not hold a repo checkout (CI runs the agent against a remote server), list `docs/adr/` through the `github` MCP instead and reconcile with the sandbox scan — take the max of both.

Slug: lowercase the title, keep `[a-z0-9]`, collapse runs to single `-`, trim, cap at ~6 words → `docs/adr/ADR-004-<slug>.md`.

### 3. Emit the ADR File
Write exactly this shape (it matches `docs/adr/ADR-002-distributed-cache-redis.md`). Every line in the metadata block ends with **two trailing spaces** — the Markdown hard break — as shown; do not let a formatter strip them.

```markdown
# ADR-004: <Title>

**Status:** ACTIVE  
**Date:** <YYYY-MM-DD merge date>  
**Author:** @<pr author login>  
**Merged in PR:** #<pr number>  
**Supersedes:** ADR-002  

## Context
<What the situation was and what forced the decision.>

## Decision
<One or two sentences. Bold the chosen technology or pattern.>

## Rationale
1. **<Reason>:** <evidence — benchmark, incident, constraint>
2. **<Reason>:** <evidence>

### Alternatives rejected
- **<Alternative>:** <why it was ruled out>

## Invariant
- **Rule:** <the MUST/MUST NEVER statement a future diff can violate>
```

(Emit `**Supersedes:**` only when this ADR replaces a prior one. Omit the `### Alternatives rejected` block if none were recorded.)

Write the file with sandbox python or a heredoc, then persist it: commit through the `github` MCP contents-write tool when the sandbox has no checkout, or write into the working tree and let the workflow's commit step push it when it does. The **Invariant** section is the load-bearing one — `cortex-detect` reasons against that sentence, so make it testable, not aspirational.

### 4. Vector Upsert
Call `upsertDecision(adr)` with the record that mirrors the file:

```jsonc
{
  "id": "ADR-004",
  "title": "…",
  "author": "@senior-dev",
  "status": "ACTIVE",
  "date": "2026-08-29",
  "merged_pr": 118,
  "scope_files": ["src/cache/**", "src/core/session.py"],
  "invariants": ["Session state MUST NOT be stored in process memory."],
  "reasoning": "…",                 // Context + Rationale, prose
  "alternatives_rejected": ["…"],
  "adr_path": "docs/adr/ADR-004-<slug>.md"
}
```

`scope_files` is what `searchDecisions(paths=…)` filters on, so record globs a future diff will actually match. Upsert is keyed on `id`; re-running ingest on the same PR must be safe.

### 5. Supersede Transition
When this ADR replaces a prior one:
1. `updateStatus(id="ADR-002", status="SUPERSEDED", superseded_by_adr="ADR-004", superseded_by_pr=118)`.
2. Rewrite the old file in the sandbox: `**Status:** SUPERSEDED` and add `**Superseded by:** ADR-004 (PR #118)` to its metadata block. Leave Context, Decision, Rationale and Invariant untouched — the history is the point.
3. Trigger `cortex-notify` for an **Architecture Drift Alert**, so the original author and the affected CODEOWNERS learn the invariant they set has been retired.

### 6. Confirmation Comment
Upsert one comment on the merged PR thread carrying the marker `<!-- codebase-cortex:pr-analysis -->` (search existing comments for the marker and update it rather than adding a second):

```markdown
<!-- codebase-cortex:pr-analysis -->
🧠 **Codebase Cortex — Decision Recorded**

- **Record:** [ADR-004: <title>](docs/adr/ADR-004-<slug>.md)
- **Author:** @<login> · **Status:** ACTIVE
- **Invariant:** <the rule>
- **Scope:** `src/cache/**`
- **Supersedes:** ADR-002 (now SUPERSEDED)

Future PRs touching this scope will be audited against the invariant above.
```

If extraction stopped at step 1, post nothing and report plainly that no ADR was warranted.
