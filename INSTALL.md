# Installation Guide

## Prerequisites

- **Python 3.11+**
- **pip** (comes with Python)

## Quick Install

### From PyPI

```bash
pip install kase-agent
```

### From Source (Development)

```bash
git clone https://github.com/kyssta-exe/kase-agent.git
cd kase-agent
pip install -e .
```

### With Extras

```bash
# Anthropic support
pip install kase-agent[anthropic]

# Messaging platform support (Telegram, Discord, etc.)
pip install kase-agent[messaging]

# Development tools
pip install kase-agent[dev]

# All extras
pip install kase-agent[anthropic,messaging,dev]
```

## Setup

### 1. Set API Keys

At minimum, set one provider API key:

```bash
# OpenAI (default)
export OPENAI_API_KEY="sk-..."

# Or Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Or any of the 31 supported providers
```

### 2. Configure (Optional)

Configuration file at `~/.kase/config.yaml` is auto-created on first run.

### 3. Verify

```bash
kase --version
kase --help
```

## Docker

```bash
docker pull kyssta/kase-agent
docker run -e OPENAI_API_KEY="sk-..." kyssta/kase-agent
```

## Windows

```powershell
# PowerShell
$env:OPENAI_API_KEY = "sk-..."
pip install kase-agent
kase
```

## Upgrading

```bash
pip install --upgrade kase-agent
```

## Troubleshooting

- **`command not found: kase`** — ensure Python's bin directory is in your PATH
- **Import errors** — verify Python 3.11+: `python --version`
- **`ModuleNotFoundError`** — try reinstalling: `pip install --force-reinstall kase-agent`
