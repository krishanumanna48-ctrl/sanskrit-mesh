"""
Sanskrit-Mesh V1 — Live Benchmark Tool

Run this to see real compression numbers on real payloads.
Paste your own JSON or use the built-in test suite.

Usage:
    python benchmark.py                    # Run full benchmark suite
    python benchmark.py --payload '{"role": "system", "content": "..."}'
    python benchmark.py --file my_payload.json
"""

import json
import sys
import argparse
import time
from compiler import SanskritMeshCompiler

compiler = SanskritMeshCompiler()


# ── ANSI Colors ───────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def print_report(label: str, original, compressed):
    report = compiler.get_savings_report(original, compressed)
    pct = report["compression_pct"]
    color = GREEN if pct >= 50 else (YELLOW if pct >= 25 else RED)

    print(f"\n{BOLD}{'─' * 60}{RESET}")
    print(f"{BOLD}{label}{RESET}")
    print(f"{'─' * 60}")
    print(f"  Original chars  : {report['original_chars']:>8}")
    print(f"  Compressed chars: {report['compressed_chars']:>8}")
    print(f"  Chars saved     : {report['chars_saved']:>8}")
    print(f"  {BOLD}Compression     : {color}{pct:>7}%{RESET}")
    print(f"  Tokens (est.)   : {report['estimated_tokens_original']:>5} → {report['estimated_tokens_compressed']:>5}  (saved {report['estimated_tokens_saved']})")
    print(f"  Cost @ GPT-4o   : ${report['estimated_cost_saved_usd_gpt4o']:.6f} saved per call")
    print(f"  Monthly (1k calls)  : ${report['monthly_savings_1k_calls_usd']:.4f} saved")
    print(f"  Monthly (100k calls): ${report['monthly_savings_100k_calls_usd']:.2f} saved")


def run_benchmark_suite():
    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  Sanskrit-Mesh V1 — Full Benchmark Suite{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}")

    results = []

    # ── Benchmark 1: Minimal Agent Message ───────────────────────────────────
    b1_orig = {
        "sender": "Agent A",
        "receiver": "Agent B",
        "intent": "Request Clarification",
        "context": {
            "status": "failed",
            "message": "I encountered the following error: NullPointerException: object reference not set. Please advise on how to proceed."
        }
    }
    b1_comp = compiler.compile_payload(b1_orig)
    print_report("Benchmark 1: Simple Agent Message", b1_orig, b1_comp)
    results.append(compiler.get_savings_report(b1_orig, b1_comp)["compression_pct"])

    # ── Benchmark 2: System Prompt ────────────────────────────────────────────
    b2_orig = (
        "You are a helpful, harmless, and honest assistant. "
        "You are operating in a multi-agent environment. "
        "Think step by step before answering. "
        "Always respond in valid JSON. "
        "Do not include any explanation outside of the JSON. "
        "Your goal is to complete the assigned task efficiently. "
        "Always Request Clarification if confused. "
        "You must complete the task using the provided tools only."
    )
    b2_comp = compiler.compile_system_prompt(b2_orig)
    print_report("Benchmark 2: System Prompt", b2_orig, b2_comp)
    results.append(compiler.get_savings_report(b2_orig, b2_comp)["compression_pct"])

    # ── Benchmark 3: LangChain Memory / Chat History ──────────────────────────
    b3_orig = {
        "history": [
            {"role": "system",    "content": "You are a senior AI agent. Always Request Clarification if confused. Use chain-of-thought reasoning for all responses."},
            {"role": "user",      "content": "Please deploy the application."},
            {"role": "assistant", "content": "I will execute the tool to deploy. Executing Tool now. The following steps were executed: Step 1: Auth check. Step 2: Build. Step 3: Deploy."},
            {"role": "tool",      "name": "DeployScript", "content": "I encountered the following error: ConnectionError: failed to establish connection. Please advise on how to proceed."},
            {"role": "assistant", "content": "The deployment failed. I encountered the following error: SyntaxError: invalid syntax. Please advise on how to proceed."},
            {"role": "user",      "content": "Fix the syntax and try again."},
            {"role": "assistant", "content": "Running again... Task Complete. The deployment succeeded."},
        ]
    }
    b3_comp = compiler.compile_payload(b3_orig)
    print_report("Benchmark 3: LangChain Memory / Chat History", b3_orig, b3_comp)
    results.append(compiler.get_savings_report(b3_orig, b3_comp)["compression_pct"])

    # ── Benchmark 4: Complex Multi-Agent Nested Payload ───────────────────────
    b4_orig = {
        "sender": "Agent A",
        "receiver": "Agent B",
        "intent": "Formulating Plan",
        "context": {
            "status": "failed",
            "history": [
                {"intent": "Executing Tool",      "message": "I encountered the following error: SyntaxError: invalid syntax. Please advise on how to proceed."},
                {"intent": "Request Clarification","message": "I encountered the following error: IndexError: list index out of range. Please advise on how to proceed."},
                {"intent": "Formulating Plan",    "message": "I will break this down into smaller steps. Let me think about this step by step."},
            ],
            "current_task": {
                "step_1": "Load massive dataset",
                "step_2": "I encountered the following error: MemoryError: out of memory.",
                "step_3": "An unexpected error occurred during execution.",
                "retry_logic": "failed",
            },
            "metadata": {
                "timestamp": "2025-01-01T00:00:00Z",
                "session_id": "abc-123",
                "model": "gpt-4o",
                "temperature": 0.7,
            }
        }
    }
    b4_comp = compiler.compile_payload(b4_orig)
    print_report("Benchmark 4: Complex Nested Multi-Agent Payload", b4_orig, b4_comp)
    results.append(compiler.get_savings_report(b4_orig, b4_comp)["compression_pct"])

    # ── Benchmark 5: ReAct Agent Scratchpad ──────────────────────────────────
    b5_orig = {
        "agent_scratchpad": (
            "Thought: Let me think about this step by step.\n"
            "I need to use a tool to answer this.\n"
            "Action: search_tool\n"
            "Action Input: query about deployment\n"
            "Observation: I encountered the following error: TimeoutError: operation timed out. Please advise on how to proceed.\n"
            "Thought: The previous step failed. Retrying.\n"
            "Action: search_tool\n"
            "Action Input: retry query\n"
            "Observation: The operation completed successfully.\n"
            "Final Answer: The deployment succeeded."
        ),
        "intermediate_steps": [
            {"action": "search_tool", "action_input": "deployment query", "observation": "result_1"},
            {"action": "search_tool", "action_input": "retry query",      "observation": "result_2"},
        ]
    }
    b5_comp = compiler.compile_payload(b5_orig)
    print_report("Benchmark 5: ReAct Agent Scratchpad", b5_orig, b5_comp)
    results.append(compiler.get_savings_report(b5_orig, b5_comp)["compression_pct"])

    # ── Benchmark 6: Worst case — all unmapped content ────────────────────────
    b6_orig = {
        "content": "The quick brown fox jumped over the lazy dog near the riverbank on a sunny afternoon.",
        "summary": "A fox and a dog. Nothing to do with agents.",
        "notes": "This payload contains zero compressible patterns and tests worst-case behavior."
    }
    b6_comp = compiler.compile_payload(b6_orig)
    print_report("Benchmark 6: Worst Case — No Dictionary Matches", b6_orig, b6_comp)
    results.append(compiler.get_savings_report(b6_orig, b6_comp)["compression_pct"])

    # ── Summary ───────────────────────────────────────────────────────────────
    avg = round(sum(results) / len(results), 2)
    best = max(results)
    worst = min(results)

    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  BENCHMARK SUMMARY{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"  Benchmarks run  : {len(results)}")
    print(f"  Best compression: {GREEN}{BOLD}{best}%{RESET}")
    print(f"  Avg compression : {YELLOW}{BOLD}{avg}%{RESET}")
    print(f"  Worst case      : {worst}%  (unmapped content — expected)")
    print(f"\n  Real-world agent pipelines sit between avg and best.")
    print(f"  For GPT-4o at scale:\n")
    avg_token_savings_per_call = round((avg / 100) * 500)  # assume avg 500 tokens/call
    print(f"    1,000 calls/day  → ~{avg_token_savings_per_call * 1000:,} tokens saved/day")
    print(f"    100k calls/month → ${round((avg_token_savings_per_call * 100_000) / 1_000_000 * 5, 2):,.2f} saved/month (GPT-4o)")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}\n")


def run_custom_payload(raw: str):
    """Run benchmark on a user-provided JSON string."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"{RED}Invalid JSON: {e}{RESET}")
        sys.exit(1)

    compressed = compiler.compile_payload(payload)
    print_report("Custom Payload", payload, compressed)
    print(f"\n{BOLD}Compressed Output:{RESET}")
    print(json.dumps(compressed, indent=2))


def run_file_payload(path: str):
    """Run benchmark on a JSON file."""
    try:
        with open(path) as f:
            payload = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"{RED}Error reading file: {e}{RESET}")
        sys.exit(1)

    compressed = compiler.compile_payload(payload)
    print_report(f"File: {path}", payload, compressed)
    print(f"\n{BOLD}Compressed Output:{RESET}")
    print(json.dumps(compressed, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sanskrit-Mesh V1 Live Benchmark")
    parser.add_argument("--payload", type=str, help="JSON string to compress and benchmark")
    parser.add_argument("--file",    type=str, help="Path to a JSON file to compress and benchmark")
    args = parser.parse_args()

    if args.payload:
        run_custom_payload(args.payload)
    elif args.file:
        run_file_payload(args.file)
    else:
        run_benchmark_suite()
 
 