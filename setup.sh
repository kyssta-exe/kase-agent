#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${KASE_VENV:-$REPO_DIR/.venv}"

# ── Colors ──────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     ${BOLD}Kase Agent Setup${NC}${CYAN}              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

# ── Find Python ─────────────────────────────────────────
PYTHON=$(command -v python3 || command -v python || echo "none")
if [ "$PYTHON" = "none" ]; then
    echo -e "${YELLOW}ERROR: Python 3 not found. Install Python 3.11+.${NC}"
    exit 1
fi
echo -e "  Python: $($PYTHON --version 2>&1)"

# ── Detect externally-managed (PEP 668) ─────────────────
EXTERNALLY_MANAGED=0
CHECK=$("$PYTHON" -c "
import sysconfig
v = sysconfig.get_config_var('EXTERNALLY_MANAGED')
print(v if v else '0')
" 2>/dev/null || echo "0")

if [ "$CHECK" = "1" ]; then
    EXTERNALLY_MANAGED=1
elif ls /usr/lib/python3*/EXTERNALLY-MANAGED 2>/dev/null; then
    EXTERNALLY_MANAGED=1
fi

if [ "$EXTERNALLY_MANAGED" = "1" ]; then
    echo -e "  ${YELLOW}Detected externally-managed Python — using venv${NC}"
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "  ${CYAN}Creating virtual environment...${NC}"
        "$PYTHON" -m venv "$VENV_DIR"
        echo -e "  ${GREEN}✓ Venv created at ${VENV_DIR}${NC}"
    fi
    PIP="$VENV_DIR/bin/pip"
    PYTHON="$VENV_DIR/bin/python"
    ACTIVATE_CMD="source $VENV_DIR/bin/activate"
else
    PIP=$(command -v pip3 || command -v pip || echo "none")
    if [ "$PIP" = "none" ]; then
        echo -e "${YELLOW}ERROR: pip not found.${NC}"
        exit 1
    fi
    ACTIVATE_CMD=""
fi

# ── Install ─────────────────────────────────────────────
echo -e "  ${CYAN}Installing Kase Agent...${NC}"
"$PIP" install --upgrade pip -q
"$PIP" install -e "$REPO_DIR"
echo -e "  ${GREEN}✓ Package installed${NC}"

# ── Install shell completions ───────────────────────────
echo -e "  ${CYAN}Installing shell completions...${NC}"
KASE_CMD="$PYTHON -m kase"
COMPLETION_DIR=""

if [ -n "${ZSH_VERSION:-}" ] || [ -n "$(command -v zsh 2>/dev/null)" ]; then
    COMPLETION_DIR="/usr/local/share/zsh/site-functions"
    if [ -d "$COMPLETION_DIR" ] 2>/dev/null; then
        $KASE_CMD completion zsh > "$COMPLETION_DIR/_kase" 2>/dev/null && \
            echo -e "  ${GREEN}✓ Zsh completion installed${NC}" || true
    fi
fi

if [ -d "/etc/bash_completion.d" ] 2>/dev/null; then
    $KASE_CMD completion bash > /etc/bash_completion.d/kase 2>/dev/null && \
        echo -e "  ${GREEN}✓ Bash completion installed${NC}" || true
elif [ -d "/usr/share/bash-completion/completions" ] 2>/dev/null; then
    $KASE_CMD completion bash > /usr/share/bash-completion/completions/kase 2>/dev/null && \
        echo -e "  ${GREEN}✓ Bash completion installed${NC}" || true
fi

# ── Done ────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Kase Agent installed successfully! ${NC}${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Quick start:${NC}"
echo "    export OPENAI_API_KEY=\"sk-...\""
echo "    kase"
echo ""
echo -e "  ${BOLD}Commands:${NC}"
echo "    kase              Interactive CLI"
echo "    kase web          Launch web dashboard"
echo "    kase setup        Setup wizard"
echo "    kase --help       All commands"
echo ""
if [ "$EXTERNALLY_MANAGED" = "1" ]; then
    echo -e "  ${YELLOW}Activate the venv:${NC}"
    echo "    $ACTIVATE_CMD"
    echo ""
fi
