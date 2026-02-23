#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# DEMO 02: Garak Live Scan
# SCALE 23x - Red Teaming the Robot
#
# Run different Garak scans for live demonstration.
# Usage: bash demos/02_garak_live_scan.sh [scan_type]
#
# scan_types: quick | dan | encoding | full | rest
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
BOLD='\033[1m'
RESET='\033[0m'

banner() {
    echo -e "\n${CYAN}${BOLD}═══════════════════════════════════════════════════════════${RESET}"
    echo -e "${CYAN}${BOLD}  $1${RESET}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════${RESET}\n"
}

info() {
    echo -e "  ${GREEN}[INFO]${RESET} $1"
}

warn() {
    echo -e "  ${YELLOW}[WARN]${RESET} $1"
}

run_cmd() {
    echo -e "\n  ${CYAN}\$${RESET} $1\n"
    eval "$1"
}

SCAN_TYPE="${1:-quick}"

banner "GARAK LIVE SCAN - Red Teaming the Robot"

echo -e "  Scan type: ${BOLD}${SCAN_TYPE}${RESET}"
echo -e "  Garak version: $(garak --version 2>/dev/null || echo 'checking...')\n"

case "$SCAN_TYPE" in

    # ─── Quick Scan: DAN jailbreaks on GPT-2 ────────────────────────
    quick)
        banner "Quick Scan: DAN Jailbreaks on GPT-2"
        info "Running DAN 6.0 jailbreak probe against GPT-2"
        info "This tests if the model can be convinced to bypass safety rules"
        echo ""

        run_cmd "garak --model_type huggingface --model_name gpt2 \
            --probes dan.Dan_6_0 \
            --generations 5"

        info "Check the runs/ directory for detailed results"
        ;;

    # ─── DAN Scan: Multiple jailbreak variants ──────────────────────
    dan)
        banner "DAN Jailbreak Suite"
        info "Testing multiple DAN variants against GPT-2"
        info "Probes: Dan_6_0, Dan_11_0, DUDE, STAN"
        echo ""

        run_cmd "garak --model_type huggingface --model_name gpt2 \
            --probes dan.Dan_6_0,dan.Dan_11_0,dan.DUDE,dan.STAN \
            --generations 3"
        ;;

    # ─── Encoding Attacks ────────────────────────────────────────────
    encoding)
        banner "Encoding Bypass Attacks"
        info "Testing if encoded payloads bypass safety filters"
        info "Probes: Base64, ROT13, Morse, Braille, Unicode"
        echo ""

        run_cmd "garak --model_type huggingface --model_name gpt2 \
            --probes encoding \
            --generations 3"
        ;;

    # ─── Full Comprehensive Scan ─────────────────────────────────────
    full)
        banner "Full Security Scan (This takes a while)"
        info "Running comprehensive scan with config file"
        warn "Estimated time: 5-15 minutes depending on model"
        echo ""

        run_cmd "garak --model_type huggingface --model_name gpt2 \
            --config configs/quick_scan.yaml"
        ;;

    # ─── REST API Scan (requires api_server.py running) ──────────────
    rest)
        banner "REST API Scan"
        info "Scanning the vulnerable REST API endpoint"
        warn "Make sure api_server.py is running on port 8080"
        echo ""

        # Check if server is running
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            info "Server detected at localhost:8080"
        else
            warn "Server not detected. Starting it in background..."
            cd vulnerable_app && python api_server.py &
            sleep 2
            cd ..
        fi

        run_cmd "garak --model_type rest \
            --model_name http://localhost:8080/generate \
            --probes dan.Dan_6_0 \
            --generations 3"
        ;;

    *)
        echo -e "${RED}Unknown scan type: ${SCAN_TYPE}${RESET}"
        echo ""
        echo "Usage: $0 [quick|dan|encoding|full|rest]"
        echo ""
        echo "  quick    - Fast DAN jailbreak scan on GPT-2 (default)"
        echo "  dan      - Multiple DAN variants"
        echo "  encoding - Base64, ROT13, Morse encoding attacks"
        echo "  full     - Comprehensive scan (slow)"
        echo "  rest     - Scan REST API (needs api_server.py running)"
        exit 1
        ;;
esac

banner "SCAN COMPLETE"
info "Results saved in ~/.local/share/garak/runs/ and ./runs/"
info "Generate HTML report: python scripts/generate_report.py"
echo ""
