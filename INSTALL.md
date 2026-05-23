# Installation Guide

## Prerequisites

- **Python 3.11+**
- **pip** (comes with Python)

## Quick Install

### One-Line Setup (Linux/macOS)

```bash
./setup.sh
```

### One-Line Setup (Windows PowerShell)

```powershell
.\setup.ps1
```

### From PyPI

```bash
pip install kase-agent
```

### From Source (Development)

```bash
git clone https://github.com/kyssta-exe/kase-agent.git
cd kase-agent
make setup          # auto-detects venv if needed
# or
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

Or use the setup script:

```powershell
.\setup.ps1
```

## Linux (Debian/Ubuntu — externally-managed)

If you see `error: externally-managed-environment`, create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Or use the auto-detecting setup script:

```bash
./setup.sh
```

## Upgrading

```bash
pip install --upgrade kase-agent
```

## Troubleshooting

- **`command not found: kase`** — ensure Python's bin directory is in your PATH
- **`error: externally-managed-environment`** — use `python3 -m venv .venv` then `source .venv/bin/activate && pip install -e .`
- **Import errors** — verify Python 3.11+: `python --version`
- **`ModuleNotFoundError`** — try reinstalling: `pip install --force-reinstall kase-agent`
