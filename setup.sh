#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${KASE_VENV:-$REPO_DIR/.venv}"

echo "==> Kase Agent Setup"
echo "    Venv: $VENV_DIR"

PYTHON=$(command -v python3 || command -v python || echo "none")
if [ "$PYTHON" = "none" ]; then
    echo "ERROR: Python 3 not found. Install Python 3.11+."
    exit 1
fi

# Detect externally-managed environment (Debian/Ubuntu PEP 668)
# Method 1: check sysconfig
EXTERNALLY_MANAGED=$("$PYTHON" -c "
import sysconfig
v = sysconfig.get_config_var('EXTERNALLY_MANAGED')
print(v if v else '0')
" 2>/dev/null || echo "0")

# Method 2: check marker file
if [ "$EXTERNALLY_MANAGED" = "0" ]; then
    MARKER=$(ls /usr/lib/python3*/EXTERNALLY-MANAGED 2>/dev/null || true)
    if [ -n "$MARKER" ]; then
        EXTERNALLY_MANAGED="1"
    fi
fi

if [ "$EXTERNALLY_MANAGED" = "1" ]; then
    echo "    Detected externally-managed Python — using venv"
    if [ ! -d "$VENV_DIR" ]; then
        echo "==> Creating virtual environment..."
        "$PYTHON" -m venv "$VENV_DIR"
    fi
    PIP="$VENV_DIR/bin/pip"
    PYTHON="$VENV_DIR/bin/python"
else
    PIP=$(command -v pip3 || command -v pip || echo "none")
    if [ "$PIP" = "none" ]; then
        echo "ERROR: pip not found."
        exit 1
    fi
fi

echo "==> Installing Kase Agent..."
"$PIP" install --upgrade pip
"$PIP" install -e "$REPO_DIR"

echo ""
echo "============================================"
echo "  Kase Agent installed successfully!"
echo "============================================"
echo ""
echo "  Quick start:"
echo "    export OPENAI_API_KEY=\"sk-...\""
echo "    kase"
echo ""
if [ "$EXTERNALLY_MANAGED" = "1" ]; then
    echo "  Activate the venv:"
    echo "    source $VENV_DIR/bin/activate"
fi
