# TrueForge — Getting Started Guide

## What is TrueForge?

TrueForge is an **open-source agent harness** that provides the runtime layer for turning an LLM into a working agent.

It brings together the pieces an agent needs to operate beyond a chat window:

| Capability | What It Does |
|---|---|
| **MCP Tools** | Connect agents to external tools and data via Model Context Protocol |
| **Skills** | Reusable git-backed instruction packs (SKILL.md files) |
| **Sandboxing** | Safe isolated environment for executing generated code |
| **Approvals** | Human-in-the-loop before sensitive actions |
| **Sub-agents** | Delegate parts of a task to parallel agents |
| **Context Management** | Manage what the agent knows and remembers |
| **Persistent Sessions** | Context carries across user sessions |

**Example Agents (Cookbook):** https://github.com/truefoundry/trueforge/tree/examples/agent-cookbook/examples

Each example is a single `agent.json`: a model, its instructions, and the connectors it's allowed to use. Copy one, point it at your own repo or database, and you have a starting agent.

---

## Step-by-Step Setup

### Step 1 — Run TrueForge

**Requirement:** Node.js 22 or newer

```bash
npx @truefoundry/trueforge
```

No additional infrastructure needed for local mode. TrueForge runs as a single process and stores data in SQLite.

Once started, open:
```
http://localhost:8790
```

> Keep it on localhost — don't expose it directly to the internet.

---

### Step 2 — Add a Model Provider

1. Open **Settings → Models**
2. Choose a model provider from the catalog
3. Configure it with your API key

After creating the provider, its models become immediately selectable when creating or running an agent.

---

### Step 3 — Connect a Tool with MCP

TrueForge uses **Model Context Protocol (MCP)** servers to connect agents to external tools and data.

1. Open **Settings → Connectors**
2. Connect an MCP server from the built-in catalog, or add your own server by URL

Once connected, your agent can **use** the tool (not just tell you how to use it).

---

### Step 4 — Add a Skill

> Tools give an agent **capabilities**. Skills give it **reusable instructions** for using those capabilities.

1. Open **Settings → Skills**
2. Enable one from the built-in list, or import a skill from GitHub

Skills are git-backed `SKILL.md` instruction packs that the agent loads when a task requires them.

---

### Step 5 — Add a Sandbox

Running generated code directly on your machine is risky. TrueForge treats the **sandbox as a tool** — the agent requests one when it needs to execute code, work with files, or use capabilities that require isolation.

TrueForge currently supports **Daytona** as a sandbox provider.

Setup:
1. Create a Daytona API key with the required permissions
2. Open **Settings → Sandbox Providers**
3. Select **Daytona**
4. Add your API key
5. Save the configuration

---

### Step 6 — Compose Your Agent

Go to chat and configure your agent:

1. Choose your model
2. Open the **Tools** menu
3. Enable capabilities:
   - **Connectors** — external tools and data
   - **Skills** — reusable instructions
   - **Dynamic sub-agents** — parallel work
   - **Sandbox** — for executing code

---

### Step 7 — Save Your Agent

1. Click **Save Agent**
2. Give it a name and instructions

Your model, connectors, skills, and instructions are all captured together. Find the saved agent in the **Agents Library** and start a new session whenever needed.
