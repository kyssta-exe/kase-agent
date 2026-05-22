# Kase — Features

## Core

- **Multi-model routing** — assign different models/providers per task category (reasoning, research, coding, agentic)
- **Caveman mode** — `/caveman [lite|normal|max|ultra]` for token-efficient responses
- **BTW / aside injection** — `/btw <message>` questions during active tasks
- **Context compression** — automatic history summarization to stay within context windows
- **Checkpoints & rollback** — filesystem state snapshots
- **Trajectory saving** — full conversation logging

## Multi-Platform Gateway

| Platform | Status |
|----------|--------|
| Terminal CLI | ✅ Native |
| TUI (Terminal UI) | ✅ Ink/React |
| Telegram | ✅ |
| Discord | ✅ |
| Slack | ✅ |
| WhatsApp | ✅ |
| Signal | ✅ |
| Matrix | ✅ |
| Mattermost | ✅ |
| Email (IMAP/SMTP) | ✅ |
| SMS | ✅ |
| DingTalk | ✅ |
| WeCom | ✅ |
| Feishu | ✅ |
| QQ Bot | ✅ |
| Webhook | ✅ |
| Home Assistant | ✅ |
| API Server | ✅ |

## Model Providers

- OpenAI / Codex
- Anthropic (direct + OAuth)
- OpenRouter
- DeepSeek
- Google Gemini
- xAI / Grok
- Together AI
- Any OpenAI-compatible endpoint via "custom" provider

## Tool System

- **Terminal** — local, Docker, SSH, Modal, Daytona, Singularity
- **File operations** — read, write, edit, patch, search
- **Web** — search (Tavily, Brave, SearXNG, Firecrawl), extract (Jina, Firecrawl, native)
- **Browser** — local Chromium, Browserbase, Browser Use cloud
- **Vision** — image analysis, OCR
- **Image generation** — FAL.ai, Replicate, local
- **TTS / STT** — ElevenLabs, OpenAI, local
- **Memory** — built-in SQLite, Honcho, Mem0, Supermemory, Hindsight, RetainDB
- **Skills** — installable workflow bundles
- **Cron** — scheduled agent runs
- **Kanban** — multi-agent work queue

## Developer Experience

- **Auto-discovery** of tools — drop a file, register, wire to toolset
- **Plugin system** — hooks (pre/post tool call, lifecycle), CLI commands, tools
- **Skin/theme engine** — YAML-defined visual themes
- **Profiles** — fully isolated instances with separate configs
- **Workspace-aware** — reads AGENTS.md / CLAUDE.md for project context
