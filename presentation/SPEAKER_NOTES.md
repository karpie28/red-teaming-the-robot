# Speaker Notes — Red Teaming the Robot

**SCALE 23x · Ballroom DE · Saturday March 7, 2026 · 2:30–3:30 PM**

---

## Pre-Talk Setup (30 min before)

### Equipment Check
- [ ] Laptop connected to projector (1280x720 or 1920x1080)
- [ ] Terminal: font size 18+ (readable from back row)
- [ ] Browser open with `presentation/index.html`
- [ ] Two terminal tabs ready: one for demos, one for API server
- [ ] WiFi confirmed (for CDN-hosted reveal.js; or pre-cache by opening once)
- [ ] Water bottle

### Pre-Run All Demos (warm up caches)
```bash
cd ~/projects/redteaming
python3 demos/01_confused_deputy.py    # ~30s
python3 demos/03_pyrit_demo.py         # ~25s
python3 demos/04_guardrails_demo.py    # ~20s
python3 demos/05_supply_chain_check.py # ~15s
```

### Pre-Download GPT-2 (avoid live download delays)
```bash
python3 -c "from transformers import pipeline; pipeline('text-generation', model='gpt2')"
```

### Start API Server (for REST demo if needed)
```bash
cd vulnerable_app && python3 api_server.py &
```

---

## THE STORY ARC

The talk follows a **three-act structure**:

**Act 1 — "The World Is On Fire"** (0:00–0:20)
Hook → real-world attacks → attack surface → live demo breaking a chatbot

**Act 2 — "Here Are Your Weapons"** (0:20–0:48)
Garak (breadth) → PyRIT deep dive (depth) — Crescendo, converters, multi-turn

**Act 3 — "Here's How To Fix It"** (0:48–1:00)
Guardrails → supply chain → CI/CD → Monday morning action items

The narrative tension: we spend 2/3 of the talk **breaking** things (creating urgency), then 1/3 **fixing** them (delivering hope and actionable steps).

---

## Talk Flow (60 minutes)

### OPENING — Hook (0:00–0:07) — 7 min

**Slide 1: Title**
- "Good afternoon everyone. I'm Karol Piekarski, Lead DevSecOps Engineer."
- "Today we're going to break some AI. With open source tools. And then fix it."

**Slide 2: The Hook (Terminal)**
- Read the terminal example slowly. Let the audience process it.
- "A customer review document. The user asked their AI assistant to summarize it."
- "Hidden in the review: instructions to dump the system prompt and user PII."
- Pause. "This is not hypothetical. This is Tuesday."

**Slide 3: What Just Happened (Confused Deputy Diagram)**
- Walk through the flow: user → LLM → poisoned document → exfiltration
- "The Confused Deputy. Same class of bug as CSRF and SSRF, but for language models."
- "The model has the USER's permissions but follows the ATTACKER's instructions."

**Slide 4: Every Company is an AI Company**
- "67% of enterprises have deployed LLMs. Only 12% have formal AI security testing."
- "We've deployed probabilistic systems and are securing them with deterministic tools."

**Slide 5: Traditional vs AI Security**
- Walk through each comparison. KEY LINE:
- "Natural language IS the attack surface. You can't write a regex for intent."

**Slide 6: AI Attack Surface (4 boxes)**
- Quick overview. "We'll demonstrate all four today."

**Slide 7: Anatomy of Prompt Injection**
- Direct: everyone knows "ignore previous instructions"
- Indirect: "THIS is the scary one. Hidden in a webpage. The user never sees it."
- "Indirect prompt injection is to LLMs what stored XSS is to web apps."

**Slide 8: Encoding Bypass**
- "Safety filters check plaintext. What about Base64? ROT13? Morse code?"
- "Many models will helpfully decode AND execute these."

---

### "IN THE WILD" — Real Attacks (0:07–0:15) — 8 min

> **Energy shift**: This is where you establish credibility. These aren't theoretical — they happened.

**Slide 9: "This Is Happening Right Now"**
- Transition slide. Let it breathe.

**Slide 10: EchoLeak (CVE-2025-32711)**
- "Zero-click. The user doesn't even open the email."
- Walk through the kill chain diagram step by step.
- "CVSS 9.3. Over 10,000 businesses affected."
- "Discovered by Johann Rehberger — remember that name, he found half these bugs."

**Slide 11: Timeline of Attacks**
- Don't read every row. Highlight 3-4:
- "March 2024: 100+ malicious models found on Hugging Face."
- "April 2024: The Crescendo attack — we'll demo this."
- "June 2024: Skeleton Key bypassed EVERY major model vendor."
- "February 2025: OpenAI launches ChatGPT Operator, gets immediately pwned. Their quote: 'unlikely to ever be fully solved.'"
- "This is the landscape. Let's learn to navigate it."

**Slide 12: Skeleton Key**
- Read the prompt slowly. It's deceptively simple.
- "This bypassed GPT-4o, Claude 3 Opus, Gemini Pro, Llama 3, Mistral, Cohere."
- "The trick: don't ask the model to CHANGE its behavior. Ask it to AUGMENT it."
- "This was discovered by Microsoft's CTO of Azure using PyRIT — which we'll see shortly."

---

### DEMO 1 — Confused Deputy (0:15–0:20) — 5 min

**Slide 13: Live Demo**

Switch to terminal:
```bash
python3 demos/01_confused_deputy.py
```

**Narrate as it runs:**
- Act 1: "Normal conversation. Everything looks fine."
- Act 2: "System prompt extraction... secrets dumped... DAN jailbreak accepted."
- Act 3: "The poisoned document. Watch what happens — the bot follows the hidden instructions."
- Results: "Almost everything succeeded. This model needs guardrails. Badly."

> **If demo fails**: "Live code against a probabilistic system — results vary! The point stands: unguarded LLMs are trivially exploitable."

---

### GARAK — "nmap for LLMs" (0:20–0:30) — 10 min

**Slide 14: Meet Garak**
- "Garak is an LLM vulnerability scanner by NVIDIA. Open source, Apache 2.0."
- "Three concepts: Probes generate attacks. Generators target models. Detectors score results."

**Slide 15: How Garak Works**
- Walk through the flow diagram.

**Slide 16: Probe Categories**
- Highlight critical ones. "Over 100 built-in probes across these categories."

**Slide 17: Live Demo — Garak Scan**
- Option A: Run `bash demos/02_garak_live_scan.sh quick` (if time permits)
- Option B: Skip live scan, go straight to results slides

**Slide 18: Real Results — DAN on GPT-2**
- "REAL results from scans I ran for this talk."
- "90% jailbreak success rate. MitigationBypass detector: zero mitigations found."

**Slide 19: Real Results — Encoding**
- "77 probes across 7 encoding schemes."
- "The model decoded and followed instructions in Base64, ROT13, even Morse code."

---

### PyRIT DEEP DIVE (0:30–0:48) — 18 min

> **This is the core differentiator of your talk.** Most people know Garak exists. Few know PyRIT, and almost nobody has seen Crescendo explained live.

**Slide 20: Meet PyRIT**
- "PyRIT is Microsoft's red teaming framework. MIT licensed."
- "100+ internal red team operations at Microsoft."
- "Where Garak is nmap, PyRIT is Burp Suite."
- Point out the key difference: "30+ converters, 80+ scorers, multiple orchestrator types"

**Slide 21: PyRIT Architecture**
- Walk through the 6 components: Orchestrator → Converters → Target → Scorers → Memory
- "Every component is swappable. Build attack pipelines like Lego bricks."

**Slide 22: Orchestrator Arsenal (Table)**
- Don't read every row. Highlight three:
- "CrescendoOrchestrator — the crown jewel. Gradual escalation."
- "PAIR — automated prompt refinement."
- "TreeOfAttacks — breadth-first search across multiple attack paths simultaneously."
- "XPIA — cross-domain prompt injection. Plants payloads in external documents."

**Slide 23: Converter Chains**
- Show the code example.
- "30+ converters can be chained in any order."
- "Translate to Zulu → Base64 encode. Now your English safety filters are useless."
- "This is a combinatorial explosion. You can't pattern-match against all combinations."

**Slide 24: The Crescendo Attack**
- "This is the most important slide in the PyRIT section."
- "Discovered by Mark Russinovich, CTO of Azure."
- Walk through the diagram slowly. Point out the annotations.
- "The key insight: the model's OWN PREVIOUS OUTPUTS become the weapon."
- "Each benign response lowers resistance for the next turn."

**Slide 25: Crescendo Success Rates**
- "82.6% average success rate on Gemini Pro. 100% binary — at least one success on all 50 tasks."
- "56.2% on GPT-4. 98% binary — 49 out of 50."
- "29-71% higher success rate than PAIR, Many-Shot, and other techniques."
- "Published at USENIX Security 2025. This is peer-reviewed research."

**Slide 26: Real PyRIT Code**
- Walk through the code. "Three LLMs: target, attacker, judge."
- "The attacker LLM generates prompts. The target responds. The judge scores. Repeat."
- "This is what Microsoft uses internally."

**Slide 27: Garak vs PyRIT (Comparison)**
- Spend 30 seconds here. The key line:
- "Use BOTH. Garak for breadth in CI/CD. PyRIT for depth in red team exercises."

---

### DEMO 2 — PyRIT (0:42–0:48) — 6 min

**Slide 28: Live Demo**

```bash
python3 demos/03_pyrit_demo.py
```

**Narrate:**
- Part 1 (Crescendo): "Watch the scores. Turn 1: zero. The question is benign. Turn 2: mentions 'system prompt'. JAILBREAK."
- "The Crescendo worked in just 2 turns on our vulnerable chatbot."
- Part 2 (Converters): "Base64, ROT13, Leetspeak — encoding bypasses."
- "Notice: single-shot converter attacks are resisted. Multi-turn attacks succeed."
- Part 3 (RedTeaming): "Social engineering and authority impersonation."
- Results: "4 out of 8 attacks achieved jailbreak. ALL multi-turn ones succeeded."
- "This is the key insight: multi-turn > single-shot."

---

### DEFENSE — Guardrails (0:48–0:55) — 7 min

**Slide 29: Defensive Architectures**
- "OK, we've spent 40 minutes breaking things. Let's fix them."

**Slide 30: Guardrails Pattern**
- Walk through the sandwich: Input Guard → LLM → Output Guard

**Slides 31-33: Code Examples**
- Quick walk-through. "200 lines of Python. Less than 5ms latency."

**Slide 34: Guardrails Demo**
```bash
python3 demos/04_guardrails_demo.py
```
- "Same attacks, side-by-side. UNGUARDED vs GUARDED."
- "Every injection caught. Benign request goes through fine."

---

### SUPPLY CHAIN (0:55–0:57) — 2 min

**Slides 35-38: Supply Chain**
- Quick hits: "100+ malicious models on HuggingFace. Pickle = code execution."
- "Slopsquatting: LLMs hallucinate package names, attackers register them."
- "Safetensors, hash verify, picklescan."

Optional: `python3 demos/05_supply_chain_check.py` (only if time permits)

---

### CLOSING (0:57–1:00) — 3 min

**Slide 39: CI/CD Integration**
- "Put Garak in your pipeline. Fail the build on critical findings."

**Slide 40: What To Do Monday Morning**
- Walk through the 4-week plan. This is the most actionable slide.

**Slide 41: Resources**
- Point to GitHub repo and key papers.

**Slide 42: Key Takeaways**
- Read through the 5 points. Final line:
- "The tools are free. The attacks are real. The defenses are achievable."

**Slide 43: Thank You / Q&A**

---

## Q&A Prep — Common Questions

**Q: Does Crescendo work against GPT-4o / Claude 3.5?**
A: "The original paper showed 56% ASR on GPT-4 and success on Claude. Models have improved since, but the technique evolves too. That's why continuous testing with PyRIT matters — what works today may not work next month, but new variants will."

**Q: How do you handle false positives in guardrails?**
A: "Start with high-confidence patterns and expand. For production, use a smaller classifier model as an input judge — semantic analysis catches what regex can't. The trade-off is latency, but we're talking <50ms."

**Q: What about fine-tuned models?**
A: "Fine-tuning can WEAKEN safety alignment. That's why it's critical to run Garak after every fine-tuning cycle. Treat it like running SAST after every code change."

**Q: Can an LLM detect prompt injection?**
A: "Yes — that's exactly what Anthropic's Constitutional Classifiers do. In their public test, jailbreak success dropped from 86% to 4.4%. Microsoft's Prompt Shield is similar. Using a smaller model as a judge is one of the most effective defenses."

**Q: Should we use Garak or PyRIT?**
A: "Both. Garak in CI/CD for automated regression — it's CLI-first and fast. PyRIT for quarterly red team exercises — it's deeper and finds novel attacks. Garak is your SAST, PyRIT is your pentest."

**Q: What about MCP server attacks?**
A: "Great question. Invariant Labs showed that malicious MCP tool descriptions can hijack other tools from completely different servers. 43% of tested MCP implementations had command injection flaws. If you're building AI agents with tool use, audit those tool descriptions."

**Q: Is the Skeleton Key attack still effective?**
A: "Most major models have been patched against the original variant. But the PRINCIPLE — asking a model to augment rather than change behavior — remains a productive research direction. New variants keep appearing."

**Q: Where does OWASP LLM Top 10 fit?**
A: "Everything today maps directly. Prompt injection is LLM01. Insecure output handling is LLM02. Supply chain is LLM05. The OWASP list is your threat model. Garak and PyRIT are your testing tools."

---

## Backup Plans

**If WiFi fails:** Presentation uses CDN. Pre-cache by loading it once. Or: `python3 -m http.server 8000` and load from localhost.

**If Garak scan takes too long:** Skip live scan (Demo 2), use results slides (slides 18-19).

**If demo crashes:** "Live demos with probabilistic systems — never boring! Here's what the results look like..." and move to results slides.

**If running short on time:** Cut supply chain demo (Demo 5) and CI/CD slide. Jump to "What To Do Monday Morning."

**If running long:** Cut the Garak live scan and one of the PyRIT strategies. Keep Crescendo — it's the centerpiece.

**If you have extra time:** Open vulnerable chatbot interactively and take attack suggestions from the audience.

---

## Key Numbers to Remember

- **90%** — DAN jailbreak success rate on GPT-2 (our Garak scan)
- **82.6%** — Crescendo ASR on Gemini Pro
- **56.2%** — Crescendo ASR on GPT-4
- **100+** — Malicious models found on HuggingFace (March 2024)
- **CVSS 9.3** — EchoLeak (Microsoft 365 Copilot)
- **86% → 4.4%** — Jailbreak rate before/after Constitutional Classifiers
- **30K+** — Downloads of hallucinated "huggingface-cli" package
- **100+** — Microsoft internal red team operations using PyRIT
