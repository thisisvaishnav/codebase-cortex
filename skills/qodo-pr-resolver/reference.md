# Qodo PR Resolver — Comment Templates

Templates used by `qodo-pr-resolver`. Every reply opens with the per-finding marker so a thread is
never answered twice:

```
<!-- codebase-cortex:qodo-fix:{finding_id} -->
```

Placeholders come only from real data — `searchDecisions` results, the Qodo finding, and the
sandbox verification output. If a value is unknown, drop the line rather than filling it in.

| Placeholder | Source |
|---|---|
| `{finding_id}` | Qodo review comment id |
| `{severity}` | `ERROR` / `WARNING` / `RECOMMENDATION` |
| `{fix_summary}` | One sentence describing the applied change |
| `{commit_sha}` | Short SHA of the pushed fix commit |
| `{verification}` | e.g. `12 tests passed, ruff clean` or `lint/typecheck only — no test suite` |
| `{adr_id}`, `{adr_title}`, `{adr_file}` | ADR record returned by `searchDecisions` |
| `{adr_author}`, `{adr_date}` | ADR metadata, verbatim |
| `{invariant}` | The ADR's Invariant, quoted verbatim |
| `{confidence}` | Integer percent from the invariant-conflict assessment |
| `{conflict_explanation}` | One or two sentences on how the suggested fix breaks the invariant |

---

## A. Inline thread reply — fix applied

```markdown
<!-- codebase-cortex:qodo-fix:{finding_id} -->
✅ **Codebase Cortex — Qodo Finding Resolved** ({severity})

{fix_summary}

- **Commit:** `{commit_sha}`
- **Verified:** {verification}
- **Architectural check:** no ACTIVE ADR invariant affected.

— *Powered by Codebase Cortex + TrueForge + Qodo*
```

---

## B. Inline thread reply — fix declined, ADR invariant conflict

Used whenever applying Qodo's suggestion would break an ACTIVE ADR invariant. No files were
changed. The ADR id, author, and invariant are mandatory here.

```markdown
<!-- codebase-cortex:qodo-fix:{finding_id} -->
🛑 **Codebase Cortex — Fix Declined: Architectural Invariant**

This finding is valid as code quality, but the suggested fix would contradict a foundational
architectural decision, so it has **not** been applied.

- **Protected Decision:** [{adr_id}: {adr_title}](docs/adr/{adr_file})
- **Decided by {adr_author} · {adr_date}**
- **Invariant:** {invariant}
- **Conflict Confidence:** {confidence}%

**Why the suggestion was not applied:** {conflict_explanation}

*To proceed anyway, {adr_id} must be superseded by a new decision record — open a PR with the
Codebase Cortex Decision Record template and tick the architectural decision box. Paging
{adr_author} for a call.*

— *Powered by Codebase Cortex + TrueForge + Qodo*
```

---

## C. Inline thread reply — skipped

One template, with `{reason}` set to the matching line:

- `Deferred — RECOMMENDATION severity; not auto-fixed by default.`
- `Not applied — the candidate patch failed sandbox verification twice: {failure_summary}`
- `Not attempted — iteration cap reached before this finding was handled.`

```markdown
<!-- codebase-cortex:qodo-fix:{finding_id} -->
⏭️ **Codebase Cortex — Finding Not Auto-Fixed** ({severity})

{reason}

Left open for a human decision.

— *Powered by Codebase Cortex + TrueForge + Qodo*
```

---

## D. PR summary comment (upserted)

Posted once per PR and updated in place — search existing comments for the marker first.

```markdown
<!-- codebase-cortex:qodo-resolution -->
🔧 **Codebase Cortex — Qodo Fix Summary**

Resolved {fixed_count} of {total_count} Qodo findings across {iterations_used} iteration(s).

| Finding | Severity | Action | Note |
|---|---|---|---|
| [`{finding_id}`]({finding_url}) | {severity} | ✅ fixed | {fix_summary} |
| [`{finding_id}`]({finding_url}) | {severity} | 🛑 declined | Protects {adr_id} ({adr_author}) |
| [`{finding_id}`]({finding_url}) | {severity} | ⏭️ skipped | {reason} |

- **Fix commits:** {commit_list}
- **Verification:** {verification}
- **Stopped because:** {stopped_because}

{open_findings_note}

— *Powered by Codebase Cortex + TrueForge + Qodo*
```

`{open_findings_note}` is omitted when nothing is left open; otherwise it names each remaining
finding and why it stayed open, so the state of the PR is never implied to be cleaner than it is.
