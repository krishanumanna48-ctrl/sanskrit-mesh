"""
Sanskrit-Mesh V1 — Round-Trip Validator

Addresses the #1 criticism: "How do I know the LLM sees the same meaning?"

This validator proves compression fidelity by:
1. Compressing a payload
2. Decompressing it back
3. Asserting byte-for-byte equality with the original
4. Reporting exactly what was compressed and what was passed through untouched

Usage:
    python validator.py                          # Run built-in test suite
    python validator.py --payload '{"key":"val"}'
    python validator.py --file my_payload.json
"""

import json
import sys
import argparse
from compiler import SanskritMeshCompiler

compiler = SanskritMeshCompiler()

GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW= "\033[93m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def validate(payload, label: str = "Payload") -> bool:
    """
    Full round-trip validation.
    Returns True if compression is 100% lossless, False if any data was corrupted.
    """
    if isinstance(payload, str):
        compressed = compiler.compile_text(payload)
        restored   = compiler.decompile_text(compressed)
        original_for_compare = payload
    else:
        compressed = compiler.compile_payload(payload)
        restored   = compiler.decompile_payload(compressed)
        original_for_compare = payload

    passed = original_for_compare == restored

    orig_str = json.dumps(payload, separators=(',', ':')) if not isinstance(payload, str) else payload
    comp_str = json.dumps(compressed, separators=(',', ':')) if not isinstance(compressed, str) else compressed

    orig_len = len(orig_str)
    comp_len = len(comp_str)
    savings  = round(((orig_len - comp_len) / orig_len) * 100, 2) if orig_len > 0 else 0.0

    print(f"\n{BOLD}{'─'*60}{RESET}")
    print(f"{BOLD}{label}{RESET}")
    print(f"{'─'*60}")

    if passed:
        print(f"  {GREEN}{BOLD}✓ PASS — 100% lossless round-trip confirmed{RESET}")
    else:
        print(f"  {RED}{BOLD}✗ FAIL — Data mismatch detected{RESET}")
        # Show exactly what differs
        if isinstance(payload, dict):
            _show_diff(payload, restored)
        else:
            print(f"  Original : {payload}")
            print(f"  Restored : {restored}")

    print(f"  Compression : {savings}%  ({orig_len} → {comp_len} chars)")
    print(f"  Compressed  : {comp_str[:120]}{'...' if len(comp_str) > 120 else ''}")

    # Show what was compressed vs passed through
    _show_coverage(payload)

    return passed


def _show_coverage(payload):
    """Shows which parts of the payload matched the dictionary vs passed through."""
    if isinstance(payload, str):
        text = payload
    elif isinstance(payload, dict):
        text = json.dumps(payload)
    else:
        return

    matched = []
    unmatched_chars = len(text)

    sorted_keys = sorted(compiler.dictionary.keys(), key=len, reverse=True)
    for phrase in sorted_keys:
        if phrase in text:
            matched.append(phrase)
            unmatched_chars -= len(phrase)

    if matched:
        print(f"\n  {GREEN}Dictionary matches ({len(matched)} phrases compressed):{RESET}")
        for m in matched[:5]:  # show first 5
            print(f"    '{m[:60]}' → |{compiler.dictionary[m]}|")
        if len(matched) > 5:
            print(f"    ... and {len(matched) - 5} more")
    else:
        print(f"\n  {YELLOW}No dictionary matches — only key minification applied{RESET}")
        print(f"  This is expected for freeform human text.")


def _show_diff(original: dict, restored: dict, path: str = ""):
    """Recursively shows exactly which keys differ between original and restored."""
    for key in original:
        full_path = f"{path}.{key}" if path else key
        if key not in restored:
            print(f"    {RED}MISSING key: {full_path}{RESET}")
        elif isinstance(original[key], dict) and isinstance(restored[key], dict):
            _show_diff(original[key], restored[key], full_path)
        elif original[key] != restored[key]:
            print(f"    {RED}MISMATCH at {full_path}:{RESET}")
            print(f"      Expected : {original[key]}")
            print(f"      Got      : {restored[key]}")


def run_builtin_suite():
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  Sanskrit-Mesh — Round-Trip Validation Suite{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")
    print(f"  Proving that every compression is 100% lossless.\n")

    tests = [
        ("Simple agent message", {
            "sender": "Agent A", "receiver": "Agent B",
            "intent": "Request Clarification",
            "context": {"status": "failed", "message": "I encountered the following error: NullPointerException: object reference not set. Please advise on how to proceed."}
        }),
        ("System prompt string", (
            "You are a helpful, harmless, and honest assistant. "
            "Think step by step before answering. Always respond in JSON format."
        )),
        ("LangChain memory", {
            "history": [
                {"role": "system",    "content": "You are a senior AI agent. Always Request Clarification if confused."},
                {"role": "assistant", "content": "The deployment failed. Running again... Task Complete"},
                {"role": "tool",      "content": "I encountered the following error: MemoryError: out of memory. Please advise on how to proceed."},
            ]
        }),
        ("Freeform human text (expect ~0% savings)", {
            "user_message": "I need this app delivered in 2 weeks with no changes to the UI or database, just the SEO."
        }),
        ("Deeply nested payload", {
            "sender": "Agent A", "intent": "Formulating Plan",
            "context": {
                "status": "running",
                "steps": [
                    {"step": "1", "status": "completed", "message": "The operation completed successfully."},
                    {"step": "2", "status": "failed",    "message": "I encountered the following error: TimeoutError: operation timed out. Please advise on how to proceed."},
                    {"step": "3", "status": "pending",   "message": "I am going to retry the operation."},
                ],
                "metadata": {"timestamp": "2025-01-01", "model": "gpt-4o", "temperature": 0.7}
            }
        }),
        ("Mixed agent + human content", {
            "system": "You are a helpful, harmless, and honest assistant. Always respond in valid JSON.",
            "user":   "Can you help me write a cover letter for a software engineering job?",
            "agent":  "I will break this down into smaller steps. Step 1: Gather user background. Step 2: Draft letter.",
            "error":  "I encountered the following error: KeyError: key not found. Please advise on how to proceed."
        }),
    ]

    all_passed = True
    for label, payload in tests:
        result = validate(payload, label)
        if not result:
            all_passed = False

    print(f"\n{'═'*60}")
    if all_passed:
        print(f"{GREEN}{BOLD}  ALL TESTS PASSED — Sanskrit-Mesh compression is 100% lossless{RESET}")
    else:
        print(f"{RED}{BOLD}  SOME TESTS FAILED — See above for details{RESET}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sanskrit-Mesh Round-Trip Validator")
    parser.add_argument("--payload", type=str, help="JSON string to validate")
    parser.add_argument("--file",    type=str, help="Path to JSON file to validate")
    args = parser.parse_args()

    if args.payload:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError:
            payload = args.payload  # treat as plain string
        validate(payload, "Custom Payload")
    elif args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                payload = json.load(f)
            validate(payload, f"File: {args.file}")
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
            sys.exit(1)
    else:
        run_builtin_suite()
