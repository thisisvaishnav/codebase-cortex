---
name: cortex-notify
description: Resolves CODEOWNERS and original decision authors, formats violation comments, and deduplicates PR comments.
---

# Cortex Notify Skill

## Overview
This skill owns every write to a GitHub thread: maintainer routing, escalation tagging, and idempotent comment updates on PRs and Issues. It is invoked by `cortex-detect` with a verdict, or by `cortex-ingest` with a drift alert. It is the only skill that posts.

Tools: the remote **`github`** MCP (plausible tool names `get_file_contents`, `list_issue_comments`, `add_issue_comment`, `update_issue_comment`; confirm against the live tool list) and your **sandbox** for parsing CODEOWNERS and hashing comment bodies. There is no filesystem MCP — read `.github/CODEOWNERS` through the `github` MCP, or from the sandbox checkout when one is present.

## Workflow

### 1. Maintainer Resolution
Read `.github/CODEOWNERS` and match it against the affected paths in the sandbox. This repository's rules are:

```
*              @lead-maintainer @senior-dev
/src/core/     @senior-dev
/src/cache/    @senior-dev
/config/       @lead-maintainer
```

Apply GitHub's real semantics, not glob intuition:
- **Last matching rule wins.** For `src/cache/session.py`, `/src/cache/` overrides `*`, so the owner is `@senior-dev` alone — not the global pair.
- A pattern with a **leading slash** is anchored at the repo root; a **trailing slash** matches everything recursively beneath that directory.
- `*` matches every file, so it is the fallback owner set for any path no specific rule claims.
- Evaluate each affected path independently, then take the **union** of the winning owner sets across all paths.
- Comment lines (`#`) and blank lines are ignored. If the file is missing or matches nothing, fall back to the ADR author alone and say so.

Then add the **original decision author**: take `author` from the violated ADR's vector record, or the `**Author:**` line of `docs/adr/ADR-XXX-*.md`. This is the person who holds the context — they lead the mention list.

### 2. Mention List Hygiene
- **Never self-tag.** Drop the current PR (or issue) author from the list. Compare logins case-insensitively with the `@` stripped — `@Senior-Dev` and `senior-dev` are the same person.
- Deduplicate, preserving order: ADR author first, then CODEOWNERS.
- Mention only when the band earns it (`confidence >= 0.80`). Advisory and clean comments carry **no** mentions at all.
- If the list empties out — the PR author is the sole owner and the ADR author — post the finding without mentions and note that the author owns the affected paths themselves.

### 3. Idempotent Comment Upserting
- Search the thread's existing comments for the hidden marker `<!-- codebase-cortex:pr-analysis -->`.
- If found: **update** that comment with the latest analysis (subject to step 5).
- If not found: **create** one.
- One marker comment per thread, forever. Never open a second, and never delete the first — its edit history is the audit trail.

### 4. Comment Formatting Template

#### A. Violation Escalation Comment:
```markdown
<!-- codebase-cortex:pr-analysis -->
⚠️ **Codebase Cortex — Architectural Conflict Detected**

This change appears to contradict a foundational architectural decision.

- **Violated Decision:** [{violated_adr_id}: {violated_adr_title}](docs/adr/{violated_adr_file})
- **Original Reasoning (by {original_author} · {time_ago}):** {original_reasoning}
- **Confidence Score:** {confidence}% ({classification})
- **Files Affected:** `{affected_files}`

🔔 **Maintainer Escalation:** Paging {original_author} and {codeowners} for architectural review.

*If this change is intentional, please update the decision record in this PR's description and tick the architectural decision checkbox.*

— *Powered by Codebase Cortex + TrueForge + Qodo*
```

#### B. Clean Audit Badge Comment:
```markdown
<!-- codebase-cortex:pr-analysis -->
✅ **Codebase Cortex — Architectural Audit Passed**

No architectural invariant conflicts detected against active ADRs.
```

For an `ADVISORY` verdict use template A's structure with a 💡 heading, no escalation line, and no mentions. For an ingest **drift alert**, use template A's structure with a 🔄 heading, state that `{new_adr_id}` (PR #{pr}) supersedes `{old_adr_id}`, and page the *retired* ADR's author plus the CODEOWNERS of its scope.

### 5. Deduplication & Cooldown
`pull_request.synchronize` fires on every push, so this skill must be able to run repeatedly and stay quiet. Before writing:

1. **Content hash.** Render the new body, then normalise it: strip the marker line, the hash footer, and any relative-time or timestamp text (`3 months ago`) — those drift on their own and would defeat the check. Hash the normalised body with sha256 in the sandbox and keep the first 12 hex chars.
2. **Compare.** Append the hash to the body as a second hidden marker: `<!-- cortex:hash:a1b2c3d4e5f6 -->`. On a re-run, read the existing marker comment, pull its embedded hash, and compare.
3. **Skip when unchanged.** Equal hashes mean the verdict is identical to what already stands — **do not call the update tool at all**. A no-op write still churns the thread's event feed and the dashboard; skipping is the correct outcome. Report "unchanged, skipped" rather than claiming a post.
4. **Escalation ratchet.** Never quietly downgrade. If the standing comment is a violation and the new verdict is clean — often because the contributor fixed the code — update it to the clean badge but keep one line recording that ADR-XXX was flagged and has been resolved. Do not re-add mentions that the standing comment already carries: editing a comment does not re-notify, but adding a *new* login does, so only mention someone the standing comment has not already paged.
5. **Quiet window.** If the standing comment was updated within the last 10 minutes and only `confidence` moved (by less than 0.05) with the same `classification` and the same `violated_adr_id`, skip the write. Substantive changes — a different classification, a different ADR, a changed file set, a crossed confidence band — always write through immediately, regardless of the window.
