# Qodo — Setup & Code Review Guide

## What is Qodo?

Qodo is an AI code review platform that reviews your code with context from the **entire repository** — not just the PR diff in isolation.

It understands:
- Repository structure
- Dependencies
- History

To surface: **bugs, risks, and standards violations**.

Available across: pull requests, IDEs, CLI, and Git workflows.

---

## Setting Up Qodo

### Step 1 — Create Your Qodo Account

Go to [app.qodo.ai/signin](https://app.qodo.ai/signin) and sign in with **Google, GitHub, or email**.

> If your team has already invited you, open the "Join your team: enjoy Qodo" email and accept the invitation before signing in.

### Step 2 — Connect Your Git Account

The setup wizard will guide you through:
1. Link your Git account (so Qodo can identify you across PRs and commits)
2. Install the **Qodo app** on your hackathon repository

### Step 3 — Connect Your Tools (Optional)

Qodo supports task management integrations:
- **Jira**
- **Linear**
- **Azure DevOps**

---

## Code Review Workflow

### Step 1 — Set Up Qodo for Your Hackathon Repository

One teammate with GitHub admin access does this once for the whole team:

```
Log in to Qodo → Integrations → SaaS → GitHub → Add installation → Connect GitHub account → Authorize your hackathon repository
```

### Step 2 — Create a Branch and Open a GitHub Pull Request

All substantive code changes should go through a PR so Qodo can review them before merging.

> ⚠️ Direct pushes to `main` do NOT count as reviewed work.

### Step 3 — Let Qodo Review Your PR

Qodo automatically starts reviewing when you open a PR. It can:
- Apply your team's coding standards
- Surface bugs, risks, and violations
- Explain and prioritize findings
- Analyze changes using context from the entire codebase

If Qodo doesn't respond automatically, comment on the PR:
```
/agentic_review
```

**Severity handling:**
- **High** — Fix all valid findings, or dismiss with a reason in the Qodo thread
- **Medium / Low** — Handle based on your engineering judgment

### Step 4 — Push Fixes and Get a Follow-Up Review

After making changes, push to the same PR and run `/agentic_review` again if needed.

### Step 5 — Add Review Proof to Your README

Create a section called:

```markdown
## Qodo Code Review Evidence
```

This section must include:
- A link to at least one representative merged PR with meaningful hackathon code
- 1–2 lines explaining what Qodo found and what you changed or intentionally dismissed
- The PR history showing the Qodo review and follow-up review

> 🔎 The public PR link is the required proof. Screenshots can add context but cannot replace the PR link.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Qodo doesn't respond | Check that the GitHub App has access to your repo and the repo is active in Qodo |
| Still nothing | Comment `/agentic_review` on the PR |

---

## Documentation Index

Full Qodo documentation index:
```
https://docs.qodo.ai/llms.txt
```

Use this file to discover all available pages before exploring further.
