---
name: qodo-get-rules
description: Collects the repository's own coding standards from Qodo config, contributor docs, and linter configs, then injects them as severity-tagged rules into the audit context.
---

# Qodo Get Rules Skill

## Overview
Loads the repository's coding standards into context **before** any architectural audit or fix
generation, so findings and patches are judged against this team's rules rather than generic ones.

There is no Qodo MCP server to query. Standards are read directly out of the repository, from the
files where the team already writes them down. Two things this skill deliberately does **not** do:

- It does not fetch findings. Qodo's own GitHub Action posts severity-ranked findings on the PR;
  those are ingested by `qodo-pr-resolver`.
- It does not carry architectural invariants. Those live in ADRs and are retrieved from the
  `cortex-vector` MCP server. Code standards and architectural invariants are separate inputs.

## Workflow

### 1. Reading the repository
Prefer the **sandbox**: in CI the repository is already checked out, so read files there and use
`ls`/`glob` to discover which of the candidates below actually exist. If no checkout is present,
fall back to the `github` MCP server's file-contents tool — inspect its advertised tool list and
use the real tool name; never guess one.

### 2. Sources, in precedence order
Later sources never override an earlier one on the same rule.

1. **Qodo configuration** — `.qodo/` (any `*.md` / `*.toml` / `*.yaml` inside it, notably a
   `best_practices.md`), plus root-level `best_practices.md`, `.qodo.toml`, `qodo.toml`,
   `.pr_agent.toml`. These are the closest thing to canonical team rules and win every conflict.
2. **Contributor and agent docs** — `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`,
   `docs/standards*.md`, `docs/style*.md`.
3. **Linter, formatter, and type configs** — `.eslintrc*`, `eslint.config.*`, `.prettierrc*`,
   `tsconfig.json` (strictness flags), `ruff.toml`, `.flake8`, `setup.cfg`,
   `pyproject.toml` (`[tool.*]` sections), `.golangci.yml`, `.pre-commit-config.yaml`,
   `.editorconfig`. These are machine-checkable and produce the most precise rules.

Read only the files that exist. Do not synthesise a rule from a file you could not open.

### 3. Normalisation
Turn every discovered rule into one record:

- `id` — short stable slug, e.g. `no-console-in-src`
- `rule` — one sentence, imperative, quoting the source's own wording where possible
- `severity` — `ERROR` | `WARNING` | `RECOMMENDATION`
- `source` — the file path it came from, so downstream comments can cite it
- `scope` — path globs or topics the rule applies to (`src/**`, `security`, `logging`)

Severity assignment:
- An explicit severity in a Qodo config or `best_practices.md` is authoritative — keep it verbatim.
- Linter levels map directly: `error`/`deny` → `ERROR`, `warn` → `WARNING`, `off` → drop the rule.
- Prose guidance maps by force of language: "must"/"never" → `ERROR`,
  "should"/"avoid" → `WARNING`, "prefer"/"consider" → `RECOMMENDATION`.

### 4. Relevance filtering
Keep a rule if either holds:
- its `scope` intersects the changed paths of the diff under audit, or
- it is cross-cutting (secrets, authentication, error handling, logging, dependency policy) —
  these are always retained regardless of the diff.

Cap the result at roughly 20 rules, `ERROR` first. The diff must stay in context; a wall of
low-value style rules that pushes it out is a net loss.

### 5. Injection into the audit context
Emit the retained rules as a single compact block, placed ahead of the diff in the audit prompt:

```markdown
## Repository Standards In Effect (N rules · source: <paths>)
- [ERROR] no-inline-secrets — Credentials must never be committed. (.qodo/best_practices.md)
- [WARNING] async-io-only — Blocking I/O should not be called from request handlers. (CONTRIBUTING.md)
```

`cortex-detect` consumes this before Stage 1 retrieval. `qodo-pr-resolver` consumes the same block
before generating any patch, so fixes do not introduce fresh standards violations.

### 6. When no rules are found
This is a normal outcome, not an error. **Proceed with the audit** and:
- set `rules_found: false` in the output contract,
- state it once, plainly, in the run log: *"No repository standards files found; auditing against
  ADR invariants only."*
- add nothing about standards to the PR comment beyond that fact.

Never invent a plausible-sounding rule, never treat missing standards as a violation, and never
block the audit waiting for them.

## Output Contract
```json
{
  "rules_found": true,
  "sources": [".qodo/best_practices.md", "CONTRIBUTING.md", "ruff.toml"],
  "rule_count": 12,
  "rules": [
    {
      "id": "no-in-process-session-state",
      "rule": "Session state must be stored in the shared cache layer, never in process memory.",
      "severity": "ERROR",
      "source": ".qodo/best_practices.md",
      "scope": ["src/**", "security"]
    }
  ],
  "dropped_for_relevance": 7
}
```
