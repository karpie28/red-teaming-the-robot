#!/usr/bin/env bash
# Pre-flight check for SCALE 23x presentation
# Run this 30 minutes before the talk to catch issues early.
#
# Usage: bash scripts/preflight.sh

RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
BOLD='\033[1m'
RESET='\033[0m'

PASS=0
FAIL=0
WARN=0

pass()  { echo -e "  ${GREEN}[PASS]${RESET} $1"; PASS=$((PASS+1)); }
fail()  { echo -e "  ${RED}[FAIL]${RESET} $1"; FAIL=$((FAIL+1)); }
warn()  { echo -e "  ${YELLOW}[WARN]${RESET} $1"; WARN=$((WARN+1)); }

echo -e "\n${CYAN}${BOLD}  SCALE 23x — Red Teaming the Robot — Pre-flight Check${RESET}\n"

# ─── Environment ────────────────────────────────────────────
echo -e "${CYAN}Environment${RESET}"

if command -v python3 &>/dev/null; then
    pass "python3 found: $(python3 --version 2>&1)"
else
    fail "python3 not found"
fi

# Check we're in the right directory
if [[ -f "presentation/index.html" ]]; then
    pass "Project root detected"
else
    fail "Not in project root (no presentation/index.html)"
    echo -e "  ${YELLOW}  Run from: cd /path/to/redteaming${RESET}"
fi

# ─── Presentation ──────────────────────────────────────────
echo -e "\n${CYAN}Presentation${RESET}"

if [[ -f "presentation/vendor/reveal.js/dist/reveal.js" ]]; then
    pass "Offline reveal.js bundle present"
else
    warn "Offline reveal.js not found — CDN required"
fi

SECTION_COUNT=$(grep -c '<section' presentation/index.html 2>/dev/null || true)
if [[ "$SECTION_COUNT" -gt 40 ]]; then
    pass "Presentation has $SECTION_COUNT section tags"
else
    warn "Only $SECTION_COUNT section tags found (expected 50+)"
fi

# Check slide IDs for emergency navigation
ID_COUNT=$(grep -c 'id="' presentation/index.html 2>/dev/null || true)
if [[ "$ID_COUNT" -ge 10 ]]; then
    pass "Slide IDs present ($ID_COUNT found)"
else
    warn "Only $ID_COUNT slide IDs — add more for emergency nav"
fi

# ─── Demos ─────────────────────────────────────────────────
echo -e "\n${CYAN}Demos (mock mode)${RESET}"

DEMOS=(
    "demos/01_confused_deputy.py"
    "demos/03_pyrit_demo.py"
    "demos/04_guardrails_demo.py"
    "demos/05_supply_chain_check.py"
    "demos/06_deepseek_attacks.py"
)

for demo in "${DEMOS[@]}"; do
    if [[ ! -f "$demo" ]]; then
        fail "$demo not found"
        continue
    fi

    start_time=$(date +%s)
    if python3 "$demo" >/dev/null 2>&1; then
        elapsed=$(( $(date +%s) - start_time ))
        pass "$demo (${elapsed}s)"
    else
        fail "$demo exited with error"
    fi
done

# Check for stray warnings in demo output
WARN_OUTPUT=$(python3 demos/01_confused_deputy.py 2>&1 | head -5)
if echo "$WARN_OUTPUT" | grep -qi "warning\|error\|traceback"; then
    warn "Demo output contains warnings — check stderr"
else
    pass "No warnings in demo output"
fi

# ─── Network (optional) ───────────────────────────────────
echo -e "\n${CYAN}Network (optional for live demos)${RESET}"

# AWS credentials (all live demos use Bedrock)
if command -v aws &>/dev/null; then
    if aws sts get-caller-identity &>/dev/null 2>&1; then
        AWS_ACCT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
        pass "AWS credentials valid (account: $AWS_ACCT)"
    else
        warn "AWS session expired — run 'aws login' before live demos"
    fi
else
    warn "AWS CLI not installed — needed for live demos"
fi

if command -v ollama &>/dev/null; then
    if ollama list 2>/dev/null | grep -q "deepseek"; then
        pass "Ollama + DeepSeek model available"
    else
        warn "Ollama installed but no deepseek model"
    fi
else
    warn "Ollama not installed — DeepSeek demo needs this or Bedrock"
fi

# ─── Terminal ──────────────────────────────────────────────
echo -e "\n${CYAN}Terminal${RESET}"

COLS=$(tput cols 2>/dev/null || echo 80)
ROWS=$(tput lines 2>/dev/null || echo 24)
if [[ "$COLS" -ge 100 ]] && [[ "$ROWS" -ge 30 ]]; then
    pass "Terminal size: ${COLS}x${ROWS}"
else
    warn "Terminal size ${COLS}x${ROWS} — recommend 120x35+"
fi

# ─── Summary ───────────────────────────────────────────────
echo -e "\n${CYAN}${BOLD}Summary${RESET}"
echo -e "  ${GREEN}$PASS passed${RESET}  ${YELLOW}$WARN warnings${RESET}  ${RED}$FAIL failed${RESET}"

if [[ "$FAIL" -gt 0 ]]; then
    echo -e "\n  ${RED}${BOLD}FIX FAILURES BEFORE PRESENTING${RESET}\n"
    exit 1
elif [[ "$WARN" -gt 0 ]]; then
    echo -e "\n  ${YELLOW}${BOLD}Warnings are OK for mock mode. Fix for live demos.${RESET}\n"
    exit 0
else
    echo -e "\n  ${GREEN}${BOLD}All clear! Ready to present.${RESET}\n"
    exit 0
fi
