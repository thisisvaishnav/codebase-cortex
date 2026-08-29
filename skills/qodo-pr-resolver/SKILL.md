---
name: qodo-pr-resolver
description: Resolves Qodo review findings on a PR by generating verified patches, but declines any fix that would break an ACTIVE ADR invariant and says so on the thread.
---

# Qodo PR Resolver Skill

## Overview
Qodo reviews the PR and posts severity-ranked findings. This skill closes the loop: it ingests
those findings, fixes the real ones, and pushes verified commits back to the PR.

The loop runs: `ingest findings → ADR gate → patch → verify in sandbox → reply + push → re-review`.

## The Architectural Veto (read this first)

**No patch is generated until the proposed fix has been checked against ADR memory.**

A code-quality suggestion is not automatically safe. Qodo sees the repository; it does not see the
reasoning that produced the architecture. "Replace this Redis round-trip with a local map, it's
faster" is a correct code-quality observation and an architectural regression at the same time.

So, for every finding, before writing a single line:

1. Build a query from the finding text, Qodo's suggested change, and the file path.
2. Call `searchDecisions` on the `cortex-vector` MCP server. Consider ACTIVE records only.
3. For each candidate at similarity ≥ 0.70, read its **Invariant** and ask the narrow question:
   *does the fix break this invariant?* — not whether the finding is related to the ADR.
4. Decide:
   - **≥ 0.80 confidence the fix breaks it** → **decline.** Do not edit any file. Reply on the
     thread with template B from `reference.md`, citing the ADR id, its author, and the invariant
     verbatim. Record `declined-architectural` with the ADR id.
   - **0.60–0.79** → attempt an alternative patch that satisfies both the finding and the
     invariant. If no such patch exists, decline as above and note the confidence is advisory.
   - **< 0.60** → proceed to patch generation.

Declining is a first-class outcome, not a failure. A silent apply that breaks an invariant is the
one thing this skill must never do — that is the entire reason it exists rather than letting Qodo's
auto-fix run unsupervised.

## Workflow

### 0. Inputs and preconditions
- Required: repository, PR number.
- Defaults: `max_iterations = 3`, `apply_recommendations = false`.
- Run `qodo-get-rules` first so patches respect repository standards.
- Read the PR with `get_pull_request` to capture the head branch, head SHA, and base. Never work
  against `main`; all commits go to the PR head branch.

### 1. Ingest findings
- `get_pull_request_reviews` for Qodo's inline review comments and their thread ids.
- `list_issue_comments` for Qodo's summary comment.
- `get_pull_request_diff` for the hunk context each finding refers to.

Attribute carefully. Only comments authored by the Qodo app are findings. Human review comments and
Cortex's own comment (marker `<!-- codebase-cortex:pr-analysis -->`) are **not** findings and must
never be auto-fixed. Skip threads that are already resolved, marked outdated, or already carry a
reply with the marker `<!-- codebase-cortex:qodo-fix:{finding_id} -->` — that thread was handled on
a previous iteration.

Normalise each finding to: `id` (the review comment id — stable across iterations), `thread_id`,
`severity`, `file`, `line`, `title`, `suggestion`.

### 2. Severity mapping
Qodo emits `ERROR` / `WARNING` / `RECOMMENDATION`; keep those as given. Where a finding is labelled
by priority instead, map `High → ERROR`, `Medium → WARNING`, `Low → RECOMMENDATION`.

Handling:
- `ERROR` — always attempt a fix.
- `WARNING` — always attempt a fix.
- `RECOMMENDATION` — **skipped by default.** Only attempt when `apply_recommendations = true`.
  Reply on the thread noting it was deferred rather than leaving it silent.

### 3. Patch generation (ERROR and WARNING, post-gate only)
- Smallest change that resolves the finding. No opportunistic refactors, no reformatting of
  untouched lines, no dependency additions unless the finding is specifically about a dependency.
- Honour the standards block from `qodo-get-rules` — a fix that trades a Qodo finding for a
  standards violation is not a fix.
- Honour the ADR invariant even when the gate cleared at low confidence.
- One fix commit per iteration, covering all patches applied in that iteration:
  `fix(qodo): resolve N findings on PR #<pr> [cortex]`.

### 4. Verify in the sandbox
Nothing is pushed unverified. In the sandbox, on a checkout of the PR head branch:

- Discover the project's own commands rather than assuming them — `package.json` scripts,
  `Makefile` targets, `pyproject.toml`, `.pre-commit-config.yaml`.
- Run, in order: formatter/linter, type check, test suite. Stop at the first failure.
- On failure: revert that finding's patch, retry once with a different approach. If it fails again,
  mark the finding `skipped` with reason `verification-failed` and move on — never push a patch
  that broke the build to satisfy a linter note.
- If the repository has no test suite, say so explicitly and mark those replies
  `verified: lint/typecheck only`. Do not claim tests passed.

### 5. Reply and push
- Reply into each inline review thread with `create_pull_request_review_comment_reply`, using the
  templates in `reference.md`. Every reply carries `<!-- codebase-cortex:qodo-fix:{finding_id} -->`
  for idempotency.
- Push the fix commit to the PR head branch. Never force-push; never rewrite existing history.
- Upsert one summary comment carrying `<!-- codebase-cortex:qodo-resolution -->` — search
  `list_issue_comments` for that marker and `update_issue_comment` if present, otherwise
  `add_issue_comment`. This marker is distinct from `codebase-cortex:pr-analysis` so the
  architectural audit comment from `cortex-notify` is never overwritten.
- Never resolve or dismiss a Qodo thread that was not actually fixed.

### 6. Loop and stop condition
The push triggers a follow-up Qodo review (comment `/agentic_review` if it does not fire). Re-ingest
and handle only **new** finding ids on the next iteration.

Stop as soon as any of these holds:
- no unhandled `ERROR` or `WARNING` findings remain;
- `max_iterations` (default 3) has been reached;
- an iteration applied no new fix — no progress means looping will not help;
- the same finding id failed verification twice.

On stopping early, the summary comment must state which findings remain open and why. Never keep
iterating in the hope that the next round differs.

## Hard rules
- Never apply a fix that breaks an ACTIVE ADR invariant, however small the diff.
- Never edit or downgrade an ADR to make a fix legal. Superseding a decision is a human call — it
  goes through a PR and `cortex-ingest`, not through this skill.
- Never cite an ADR id, author, or invariant that `searchDecisions` did not return.
- Never push to `main`, never force-push, never touch files outside the PR's scope.

## Output Contract
```json
{
  "pr": 142,
  "iterations_used": 2,
  "commits": ["a1b2c3d", "e4f5a6b"],
  "findings": [
    {
      "id": "1998877665",
      "severity": "ERROR",
      "action": "fixed",
      "file": "src/api/handlers.py",
      "summary": "Added timeout and retry to the outbound billing call.",
      "verified": "tests+lint"
    },
    {
      "id": "1998877701",
      "severity": "WARNING",
      "action": "declined-architectural",
      "file": "src/cache/session.py",
      "adr_id": "ADR-002",
      "summary": "Suggested swapping Redis for an in-process dict; violates the session-persistence invariant."
    },
    {
      "id": "1998877742",
      "severity": "RECOMMENDATION",
      "action": "skipped",
      "reason": "recommendation-deferred"
    }
  ],
  "open_findings": [],
  "stopped_because": "no-remaining-error-or-warning"
}
```

`action` is one of `fixed`, `declined-architectural`, `skipped`. `adr_id` is required whenever
`action` is `declined-architectural`, and must be omitted otherwise. `reason` is required for
`skipped` (`recommendation-deferred`, `verification-failed`, `iteration-cap`).

## Reference
Comment and reply templates: `reference.md` in this skill directory.
