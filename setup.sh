#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${KASE_VENV:-$REPO_DIR/.venv}"

echo "==> Kase Agent Setup"
echo "    Venv: $VENV_DIR"

# Detect externally-managed environment (Debian/Ubuntu PEP 668)
PYTHON=$(command -v python3 || command -v python)
if $PYTHON -c "import sysconfig; print(sysconfig.get_config_var('EXTERNALLY_MANAGED'))" 2>/dev/null | grep -q 1; then
    echo "    Detected externally-managed Python — using venv"
    USE_VENV=1
else
    USE_VENV=0
fi

# Create venv if needed
if [ "$USE_VENV" = "1" ] && [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
    echo "    Activate with: source $VENV_DIR/bin/activate"
fi

# Determine pip
if [ "$USE_VENV" = "1" ]; then
    PIP="$VENV_DIR/bin/pip"
    PYTHON="$VENV_DIR/bin/python"
else
    PIP=$(command -v pip3 || command -v pip)
fi

echo "==> Installing Kase Agent..."
"$PIP" install --upgrade pip
"$PIP" install -e "$REPO_DIR"

# Install extras based on available packages
echo "==> Checking optional dependencies..."
if $PYTHON -c "import anthropic" 2>/dev/null; then
    "$PIP" install -e "$REPO_DIR[anthropic]"
fi

echo ""
echo "============================================"
echo "  Kase Agent installed successfully!"
echo "============================================"
echo ""
echo "  Quick start:"
echo "    export OPENAI_API_KEY=\"sk-...\""
echo "    kase"
echo ""
if [ "$USE_VENV" = "1" ]; then
    echo "  Remember to activate the venv:"
    echo "    source $VENV_DIR/bin/activate"
fi
