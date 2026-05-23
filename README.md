# Kase Agent

**Next-generation AI agent by Kyssta.** Smarter, faster, and more optimized than any other agent framework.

## Features

- **31 LLM providers** — OpenAI, Anthropic, Gemini, Grok, DeepSeek, and 26 more
- **35+ built-in tools** — file I/O, terminal, web, browser automation, code execution, image gen, TTS, vision, kanban, cron, and more
- **Multi-model routing** — route tasks to the best model for the job (reasoning, coding, agentic, image gen)
- **Multi-platform messaging** — Telegram, Discord, Slack, WhatsApp, Matrix, email, Teams, and 20+ more via the gateway layer
- **Long-term memory** — persistent, extractable, searchable memory across sessions
- **Plugin & skill system** — extend functionality with plugins and reusable skills
- **Web dashboard** — real-time analytics panel
- **ACP server** — editor integration (JSON-RPC)
- **CLI with skins** — themed interactive REPL

## Quick Start

```bash
# Install
pip install kase-agent

# Or from source
git clone https://github.com/kyssta-exe/kase-agent.git
cd kase-agent
pip install -e .

# Set your API key
export OPENAI_API_KEY="sk-..."

# Run it
kase
```

## Documentation

| Topic | Location |
|-------|----------|
| Installation | [INSTALL.md](INSTALL.md) |
| CLI commands | `kase --help` |
| Configuration | `~/.kase/config.yaml` |
| Provider setup | `kase/agents/providers/` |

## Architecture

```
kase/
├── agent/          # Core agent loop, memory, routing
├── tools/          # Tool implementations (35+)
├── providers/      # 31 LLM provider profiles
├── gateway/        # Multi-platform messaging
├── cli/            # Interactive REPL
├── web_panel/      # Analytics dashboard
├── plugins/        # Plugin system
├── skills/         # Skill system
├── kanban/         # Multi-agent coordination
├── cron/           # Job scheduling
└── acp/            # Editor integration
```

## Requirements

- Python 3.11+
- An API key for at least one LLM provider

## License

MIT
