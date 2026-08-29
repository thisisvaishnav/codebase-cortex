# Hackathon Overview

## Event Details

| Field | Info |
|-------|------|
| **Name** | The Agent Harness Hackathon |
| **Duration** | August 24–30, 2026 |
| **Prize Pool** | $10,000 |
| **Organizer** | WeMakeDevs × TrueFoundry |
| **Source Blog** | https://www.wemakedevs.org/blogs/agent-harness-hackathon-kick-off |
| **Author** | Sachin Sharma |

## What Is This Hackathon?

Build a useful AI agent using:
- **TrueForge** — TrueFoundry's open-source agent harness (the runtime layer)
- **Qodo** — AI code review platform (used throughout development, not just at the end)

> This is NOT about building another chat interface around an LLM.

## The Core Challenge

**Two-sided problem:**

1. **Agent side** — Can your agent _do_ something genuinely useful? (not just generate answers)
2. **Code quality side** — Is the codebase readable, reviewable, and continuable by someone else?

## The Gap To Solve

LLMs are good at **explaining** what to do. The hard part is building systems that reliably **do the work**:

- Retrieving information from external tools
- Working with APIs or data sources
- Executing generated code
- Processing files or data
- Delegating parts of a task to sub-agents
- Carrying context across sessions
- Stopping and asking a human before sensitive actions

## What You Can Build

Any workflow where a human currently:
- Gathers information
- Makes decisions
- Moves between multiple tools
- Manually performs a series of actions

### Example Project Ideas

| Project Type | What the Agent Does |
|---|---|
| **DevOps Agent** | Inspect systems via MCP, split investigation to sub-agents, run diagnostics in sandbox, propose fix, ask before sensitive actions |
| **Research Agent** | Gather info via external tools, assign subtasks to sub-agents, process findings, persist context across sessions |
| **Data Workflow Agent** | Collect inputs, generate code, execute in sandbox, inspect output, decide next step |
| **Engineering Workflow Agent** | Gather repo context, use engineering tools, run/test code in isolation, ask before risky actions |
| **Operations Agent** | Follow skills-based instructions, gather info, perform safe actions automatically, pause for human confirmation |

> These are just examples. The important pattern: **agent does work, not just generates an answer**.

## Connect With Us

- Website: https://www.wemakedevs.org
- Email: contact@wemakedevs.org
