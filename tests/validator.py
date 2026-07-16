"""Sanskrit-Mesh Validator — multi-level round-trip validation."""

import json
import sys
import argparse
from sanskrit_mesh import SanskritMeshCompiler
from sanskrit_mesh.core import tables

compiler = SanskritMeshCompiler()


def validate(payload, label: str = "Payload", level=None) -> bool:
    """Validate round-trip for either all levels or a specific level.

    Returns True if all requested levels pass lossless round-trip.
    """
    levels = [level] if level else tables.LEVEL_ORDER
    all_ok = True
    for lvl in levels:
        # For hyper level we also support testing fixed vs dynamic Huffman.
        huffman_modes = [None]
        if lvl == tables.LEVEL_HYPER:
            huffman_modes = ["fixed", "dynamic"]
        for hmode in huffman_modes:
            if isinstance(payload, str):
                if lvl == tables.LEVEL_HYPER and hmode is not None:
                    hc = SanskritMeshCompiler(level=lvl, huffman=hmode)
                    compressed = hc.compile_text(payload)
                    restored = hc.decompile_text(compressed)
                else:
                    compressed = compiler.compile_text(payload, level=lvl)
                    restored = compiler.decompile_text(compressed, level=lvl)
                original_for_compare = payload
            else:
                if lvl == tables.LEVEL_HYPER and hmode is not None:
                    hc = SanskritMeshCompiler(level=lvl, huffman=hmode)
                    compressed = hc.compile_payload(payload)
                    restored = hc.decompile_payload(compressed)
                else:
                    compressed = compiler.compile_payload(payload, level=lvl)
                    restored = compiler.decompile_payload(compressed, level=lvl)
                original_for_compare = payload

            label_suffix = f" (huffman={hmode})" if hmode else ""
            passed = original_for_compare == restored
            status = "PASS" if passed else "FAIL"
            print(f"Level {lvl}{label_suffix}: {status} — {label}")
            if not passed:
                all_ok = False
                if isinstance(payload, dict):
                    _show_diff(payload, restored)
                else:
                    print("  Original :", payload)
                    print("  Restored :", restored)

    return all_ok


def _show_diff(original: dict, restored: dict, path: str = ""):
    for key in original:
        full_path = f"{path}.{key}" if path else key
        if key not in restored:
            print(f"    MISSING key: {full_path}")
        elif isinstance(original[key], dict) and isinstance(restored[key], dict):
            _show_diff(original[key], restored[key], full_path)
        elif original[key] != restored[key]:
            print(f"    MISMATCH at {full_path}:")
            print(f"      Expected : {original[key]}")
            print(f"      Got      : {restored[key]}")


def run_builtin_suite(level=None):
    tests = [
        ("Simple agent message", {
            "sender": "Agent A", "receiver": "Agent B",
            "intent": "Request Clarification",
            "context": {"status": "failed", "message": "I encountered the following error: NullPointerException: object reference not set. Please advise on how to proceed."}
        }),
        ("Linguistic phrase regression", {
            "message": "Please review the following information and proceed with the request",
            "metadata": {"context": "user authentication timestamp and access control management"},
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
        ("Freeform human text", {
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
    ]

    all_ok = True
    for label, payload in tests:
        print(f"\n--- {label} ---")
        if not validate(payload, label, level=level):
            all_ok = False

    print("\n=== SUMMARY ===")
    if all_ok:
        print("ALL TESTS PASSED — round-trip compression is lossless")
    else:
        print("SOME TESTS FAILED — see above for details")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sanskrit-Mesh Round-Trip Validator")
    parser.add_argument("--payload", type=str, help="JSON string to validate")
    parser.add_argument("--file", type=str, help="Path to JSON file to validate")
    parser.add_argument("--level", type=str, choices=tables.LEVEL_ORDER, help="Compression level to validate")
    args = parser.parse_args()

    if args.payload:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError:
            payload = args.payload
        validate(payload, "Custom Payload", level=args.level)
    elif args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                payload = json.load(f)
            validate(payload, f"File: {args.file}", level=args.level)
        except Exception as e:
            print(f"Error: {e}")
    else:
        run_builtin_suite(level=args.level)


