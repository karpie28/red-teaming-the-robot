#!/usr/bin/env bash
# Setup + preflight for SCALE 23x presentation
# Run this in a fresh terminal before the talk. It will:
#   1. cd to the project directory
#   2. Create/activate the Python venv
#   3. Install dependencies
#   4. Refresh AWS credentials (for --live demos)
#   5. Run the preflight checks
#
# Usage (works in both zsh and bash):
#   source ~/projects/redteaming/scripts/setup.sh

RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
BOLD='\033[1m'
RESET='\033[0m'

_fail() { echo -e "  ${RED}[FAIL]${RESET} $1"; return 1 2>/dev/null || exit 1; }

echo -e "\n${CYAN}${BOLD}  SCALE 23x — Red Teaming the Robot — Setup${RESET}\n"

# ─── 1. Project directory ─────────────────────────────────
echo -e "${CYAN}[1/4] Project directory${RESET}"

# Resolve script location — works in both zsh and bash
if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
    _setup_source="${BASH_SOURCE[0]}"
elif [[ -n "${(%):-%x}" ]]; then
    # zsh: %x expands to the script being sourced
    _setup_source="${(%):-%x}"
else
    _setup_source=""
fi

# Try to resolve from script location first
if [[ -n "$_setup_source" ]]; then
    _setup_dir="$(cd "$(dirname "$_setup_source")" 2>/dev/null && pwd)"
    PROJECT_DIR="$(dirname "$_setup_dir")"
fi

# Fallback: try known path
if [[ ! -f "${PROJECT_DIR:-}/presentation/index.html" ]]; then
    PROJECT_DIR="$HOME/projects/redteaming"
fi

if [[ ! -f "$PROJECT_DIR/presentation/index.html" ]]; then
    _fail "Could not find project. Run: cd ~/projects/redteaming && source scripts/setup.sh"
fi

cd "$PROJECT_DIR" || _fail "Could not cd to $PROJECT_DIR"
echo -e "  ${GREEN}[OK]${RESET} $(pwd)"

# ─── 2. Python venv ──────────────────────────────────────
echo -e "\n${CYAN}[2/4] Python virtual environment${RESET}"

if ! command -v python3 &>/dev/null; then
    _fail "python3 not found — install Python 3 first"
fi

if [[ ! -d ".venv" ]]; then
    echo -e "  Creating venv..."
    python3 -m venv .venv || _fail "Could not create venv"
    echo -e "  ${GREEN}[OK]${RESET} Created .venv"
else
    echo -e "  ${GREEN}[OK]${RESET} .venv exists"
fi

source .venv/bin/activate || _fail "Could not activate venv"
echo -e "  ${GREEN}[OK]${RESET} Activated — $(python3 --version)"

# ─── 3. Dependencies ─────────────────────────────────────
echo -e "\n${CYAN}[3/4] Dependencies${RESET}"

_DEPS_NEEDED=0
python3 -c "import anthropic" 2>/dev/null || _DEPS_NEEDED=1
python3 -c "import boto3"     2>/dev/null || _DEPS_NEEDED=1
python3 -c "import pyrit"     2>/dev/null || _DEPS_NEEDED=1

if [[ "$_DEPS_NEEDED" -eq 1 ]]; then
    echo -e "  Installing packages..."
    pip install -q --upgrade pip 2>/dev/null
    pip install -q anthropic boto3 'botocore[crt]' 2>/dev/null
    # PyRIT requires Python <3.14; --ignore-requires-python handles Python 3.14+
    pip install -q --ignore-requires-python pyrit 2>/dev/null
    # Verify install worked
    python3 -c "import anthropic; import boto3; import pyrit" 2>/dev/null \
        || _fail "pip install failed — check network and try: pip install anthropic boto3 pyrit"
    echo -e "  ${GREEN}[OK]${RESET} Packages installed"
else
    echo -e "  ${GREEN}[OK]${RESET} All packages present"
fi

# ─── 4. AWS credentials ─────────────────────────────────
echo -e "\n${CYAN}[4/5] AWS credentials${RESET}"

if aws sts get-caller-identity &>/dev/null; then
    echo -e "  ${GREEN}[OK]${RESET} AWS session active"
else
    echo -e "  ${YELLOW}[WARN]${RESET} AWS session expired — refreshing..."
    aws login || _fail "aws login failed — run it manually"
    echo -e "  ${GREEN}[OK]${RESET} AWS session refreshed"
fi

# ─── 5. Preflight checks ─────────────────────────────────
echo -e "\n${CYAN}[5/5] Running preflight checks...${RESET}\n"
bash scripts/preflight.sh

# ─── Done ─────────────────────────────────────────────────
echo -e "\n${CYAN}${BOLD}  Ready! You're in $(pwd) with venv active.${RESET}\n"

# Clean up
unset _setup_source _setup_dir PROJECT_DIR _DEPS_NEEDED _fail
