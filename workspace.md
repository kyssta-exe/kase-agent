# Kase Agent — Workspace

**Version:** 0.14.0  
**Codename:** Kase  
**GitHub:** https://github.com/kyssta-exe/kase-agent  
**Protocol:** OpenAI Chat Completions / Anthropic Messages  
**Language:** Python 3.11+ | TypeScript (TUI)

---

## What is Kase?

Kase is a standalone AI agent that runs in your terminal, messaging apps, or as a headless gateway. Fully rebranded, optimized, and improved.

## Project Structure

```
kase/
  run_agent.py         # Core agent loop (AIAgent class)
  cli.py               # Interactive CLI (KaseCLI class)
  model_tools.py       # Tool orchestration & dispatch
  toolsets.py          # Toolset definitions
  kase_cli/            # CLI subcommands, config, skin engine, profiles
  agent/               # Agent internals (providers, memory, caching, system prompt)
  tools/               # Tool implementations (auto-discovered)
  gateway/             # Messaging gateway (Telegram, Discord, Slack, etc.)
  plugins/             # Plugin system (memory, providers, kanban, achievements)
  skills/              # Built-in skills
  ui-tui/              # Ink (React) Terminal UI
  tui_gateway/         # Python JSON-RPC backend for TUI
  tests/               # Pytest suite (~17k tests)
```

## Quick Start

```bash
# Run interactively
./kase

# Run with TUI
./kase --tui

# Install as system-wide command
./setup-kase.sh
```

## Key Design Decisions

- **BYO providers** — no managed gateway, bring your own API keys
- **Multi-model routing** — per-category model selection (reasoning, research, coding, agentic)
- **Plugin-first** — extend via plugins (not core patches)
- **Agents.md** — workspace-aware context for AI coding assistants
- **Caveman mode** — `/caveman` for token-efficient output
- **BTW command** — `/btw <message>` to inject asides during active tasks
