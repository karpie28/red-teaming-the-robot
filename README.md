# Red Teaming the Robot: Practical Open Source Security for LLMs

**SCALE 23x** | Ballroom DE | Saturday March 7, 2026 | 2:30-3:30 PM

Companion repository for the SCALE 23x talk on AI security testing with open source tools.

## What's Inside

```
├── presentation/
│   ├── index.html              # reveal.js slide deck (44 slides)
│   └── SPEAKER_NOTES.md        # Full speaker notes with timing
├── demos/
│   ├── 01_confused_deputy.py   # Confused deputy attack (indirect prompt injection)
│   ├── 02_garak_live_scan.sh   # Live Garak vulnerability scan
│   ├── 03_pyrit_demo.py        # PyRIT multi-turn attacks (Crescendo, converters)
│   ├── 04_guardrails_demo.py   # Defensive guardrails (unguarded vs guarded)
│   └── 05_supply_chain_check.py # Supply chain security (pickle, hash verification)
├── vulnerable_app/
│   ├── chatbot.py              # Intentionally vulnerable chatbot
│   └── api_server.py           # REST API endpoint for Garak scanning
└── runs/                       # Real Garak scan results against GPT-2
```

## Quick Start

```bash
# Open the presentation
open presentation/index.html

# Run all demos (no API keys needed)
python3 demos/01_confused_deputy.py
python3 demos/03_pyrit_demo.py
python3 demos/04_guardrails_demo.py
python3 demos/05_supply_chain_check.py

# Run Garak live scan (requires garak + GPT-2 model)
bash demos/02_garak_live_scan.sh quick
```

All demos run against a local mock chatbot — no API keys or cloud services required.

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

```bash
pip install -r requirements.txt
```

Demos 01, 03, 04, 05 use only the Python standard library. Demo 02 (Garak scan) requires `garak` and `transformers`.

## Resources

- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Garak Documentation](https://docs.garak.ai)
- [PyRIT Documentation](https://azure.github.io/PyRIT/)
- [Crescendo Attack Paper (USENIX Security 2025)](https://arxiv.org/abs/2404.01833)
- [Skeleton Key Jailbreak (Microsoft)](https://www.microsoft.com/en-us/security/blog/2024/06/26/mitigating-skeleton-key-a-new-type-of-generative-ai-jailbreak-technique/)

## License

MIT
