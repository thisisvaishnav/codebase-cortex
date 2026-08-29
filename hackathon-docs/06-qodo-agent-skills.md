# Qodo Agent Skills

> Source: https://docs.qodo.ai/agent-skills

## What Are Agent Skills?

Skills are **reusable, agent-agnostic instruction sets** that extend what your AI coding agent can do.

Each skill is a plain-text file that tells the agent how to complete a specific task, such as:
- Fetching rules
- Resolving review comments
- Executing other codified engineering actions

Skills follow the open **Agent Skills standard**, making them portable across compatible agents.

**Compatible agents:** Claude Code, Cursor, Windsurf, Cline, and any agent supporting the Agent Skills standard.

Skills are maintained as an **open-source project on GitHub** and can be installed directly from the repository.

---

## How Skills Are Executed

1. When you install a skill, it is placed in a directory monitored by your agent
2. It becomes available as a **named command**
3. Each skill is defined in a plain-text `SKILL.md` file
4. When invoked, your agent reads these instructions and executes them
5. The agent interacts with Qodo services or your Git provider as needed
6. Results are returned in the conversation

---

## Core Qodo Skills

### `qodo-get-rules`

**Purpose:** Fetches your repository-specific coding rules from the Qodo platform so your agents write code aligned with your standards from the start.

**Key Features:**
- Retrieves only relevant rules using semantic matching
- Applies severity levels: `ERROR`, `WARNING`, `RECOMMENDATION`
- Combines topic-based and cross-cutting rule retrieval
- Designed to run **before** code generation, editing, or refactoring

**Recommended Use:** Run before writing or modifying code so rules are already in context, reducing issues before they appear.

---

### `qodo-pr-resolver`

**Purpose:** Fetches open Qodo review findings from your Git provider and helps resolve them interactively or in batch using local Git CLI operations, keeping pull requests clean and up to date.

**Key Features:**
- Works across **GitHub, GitLab, Bitbucket, Azure DevOps**
- Interactive issue review and auto-fix modes
- Inline comment handling with automated commits
- Severity mapping from Qodo's action levels
- Automatic PR/MR summary comments

**Recommended Use:** Verify automated summaries before merging. The skill posts fix documentation and replies to inline comments automatically — do a quick review to ensure responses are accurate.

---

## Installing Qodo Skills

Install all Qodo skills in your agent:

```bash
npx skills add qodo-ai/qodo-skills/skills
```

For hackathon-specific setup (install from Codex):
```bash
npx skills add qodo-ai/qodo-skills/skills
```

Then in Codex, run `/skills` to confirm `qodo-pr-resolver` is available.

**GitHub Repository:** https://github.com/qodo-ai/qodo-skills

---

## Using `qodo-pr-resolver` with a Coding Agent

The workflow for fixing Qodo findings with a coding agent:

### Step 1 — Install the skill (once)

```bash
npx skills add qodo-ai/qodo-skills/skills
```

In Codex, run `/skills` to confirm `qodo-pr-resolver` is available.

### Step 2 — Invoke the skill

```
$qodo-pr-resolver Resolve the Qodo findings for the PR on my current branch. Show the issues first, then let me review each one or auto-fix all.
```

### Step 3 — Review proposed fixes

- Run the repository's tests
- Approve or defer each finding with a reason
- The skill can create fix commits, reply to Qodo's inline threads, and post a Qodo Fix Summary on the PR

### Step 4 — Push the fixes

GitHub shows:
- Fix commits
- Thread replies
- Fix Summary (visible remediation evidence)

The push should trigger a follow-up review. If not, comment `/agentic_review`.

**The loop:** `resolver → code change → tests → push → GitHub evidence → Qodo re-review`

---

## Why Use Skills?

Instead of limiting quality checks to pull requests, Skills **shift quality and governance left** by:
- Applying your defined rules as you write code
- Surfacing issues early
- Helping address feedback directly inside the tools you already use
