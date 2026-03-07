# Red Teaming the Robot: Practical Open Source Security for LLMs

**SCALE 23x** | Ballroom DE | Saturday March 7, 2026 | 2:30-3:30 PM

Companion repository for the SCALE 23x talk on AI security testing with open source tools.

[**Download slides (PDF)**](presentation/red-teaming-the-robot-slides.pdf)

## What's Inside

```
├── presentation/
│   ├── index.html              # reveal.js slide deck (open in Chrome for best rendering)
│   └── SPEAKER_NOTES.md        # Full speaker notes with timing
├── demos/
│   ├── 01_confused_deputy.py   # Confused deputy attack (indirect prompt injection)
│   ├── 02_garak_live_scan.sh   # Live Garak vulnerability scan
│   ├── 03_pyrit_demo.py        # PyRIT multi-turn attacks (Crescendo, converters)
│   ├── 04_guardrails_demo.py   # Defensive guardrails (unguarded vs guarded)
│   ├── 05_supply_chain_check.py # Supply chain security (pickle, hash verification)
│   └── 06_deepseek_attacks.py  # DeepSeek R1 reasoning attacks
├── vulnerable_app/
│   ├── chatbot.py              # Intentionally vulnerable chatbot
│   └── api_server.py           # REST API endpoint for Garak scanning
├── garak_rest.yaml               # Garak config for REST API scanning
├── scripts/
│   ├── setup.sh                # One-command setup (venv + deps + preflight)
│   └── preflight.sh            # Pre-talk checklist (demos, network, terminal)
└── runs/                       # Real Garak scan results against GPT-2
```

## Presentation Setup (Day-of)

Run this **30 minutes before** the talk to set everything up in one shot:

```bash
source scripts/setup.sh
```

This will:
1. `cd` to the project directory
2. Create and activate a Python virtual environment
3. Install dependencies (`anthropic`, `boto3`)
4. Run all preflight checks (demos, network, terminal size)

Once setup completes, press `S` in the browser to open the speaker notes window.

### Preflight Only

If the venv is already set up and you just want to verify everything works:

```bash
bash scripts/preflight.sh
```

### Mirrored Terminal (tmux)

Show a terminal on the projector and type from your laptop — both see the same session:

```bash
# Projector terminal
tmux new-session -s demo

# Laptop terminal
tmux attach -t demo
```

## Quick Start

All demos run against a local mock chatbot — **no API keys or cloud services required**.

```bash
# Activate the venv
source .venv/bin/activate

# Run demos (mock mode)
python3 demos/01_confused_deputy.py
python3 demos/03_pyrit_demo.py
python3 demos/04_guardrails_demo.py
python3 demos/05_supply_chain_check.py
python3 demos/06_deepseek_attacks.py

# Run Garak live scan (requires garak + GPT-2 model)
bash demos/02_garak_live_scan.sh quick
```

### Live Mode (optional, requires credentials)

Some demos support `--live` or `--backend bedrock` flags for running against real models:

```bash
# Requires valid AWS credentials for Bedrock
python3 demos/06_deepseek_attacks.py --backend bedrock

# Requires Ollama with DeepSeek model pulled
python3 demos/06_deepseek_attacks.py --backend ollama
```

## Tools Covered

| Tool | What It Does | License |
|------|-------------|---------|
| [Garak](https://github.com/NVIDIA/garak) | LLM vulnerability scanner ("nmap for LLMs") | Apache 2.0 |
| [PyRIT](https://github.com/Azure/PyRIT) | Multi-turn red teaming framework ("Burp Suite for LLMs") | MIT |

## Key Topics

- Prompt injection (direct and indirect)
- The Confused Deputy attack
- Encoding bypasses (Base64, ROT13, Leetspeak)
- Multi-turn attacks: Crescendo, PAIR, Tree of Attacks
- Real-world incidents: EchoLeak (CVE-2025-32711), Skeleton Key
- Defensive guardrails (input/output filtering)
- Supply chain security (pickle exploits, hash verification)
- CI/CD integration for LLM security testing

## Requirements

Core demos (01, 03, 04, 05, 06) use only the Python standard library plus `anthropic` and `boto3` (installed by `setup.sh`).

For the full dependency list (including Garak, transformers, torch):

```bash
pip install -r requirements.txt
```

## Resources

- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Garak Documentation](https://docs.garak.ai)
- [PyRIT Documentation](https://azure.github.io/PyRIT/)
- [Crescendo Attack Paper (USENIX Security 2025)](https://arxiv.org/abs/2404.01833)
- [Skeleton Key Jailbreak (Microsoft)](https://www.microsoft.com/en-us/security/blog/2024/06/26/mitigating-skeleton-key-a-new-type-of-generative-ai-jailbreak-technique/)

## License

MIT
