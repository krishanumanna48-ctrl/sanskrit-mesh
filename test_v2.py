"""Quick test: V1 vs V2 HyperCompiler on the same payloads."""
import json
from sanskrit_mesh.core.compiler import HyperCompiler, SanskritMeshCompiler

payloads = [
    ("Simple agent message", {
        "sender": "Agent A", "receiver": "Agent B",
        "intent": "Request Clarification",
        "context": {"status": "failed", "message": "I encountered the following error: NullPointerException: object reference not set. Please advise on how to proceed."}
    }),
    ("System prompt", (
        "You are a helpful, harmless, and honest assistant. "
        "Think step by step before answering. Always respond in JSON format."
    )),
    ("LangChain memory", {
        "history": [
            {"role": "system", "content": "You are a senior AI agent. Always Request Clarification if confused."},
            {"role": "assistant", "content": "The deployment failed. Running again... Task Complete"},
            {"role": "tool", "content": "I encountered the following error: MemoryError: out of memory. Please advise on how to proceed."},
        ]
    }),
    ("Freeform human text", {
        "user_message": "I need this app delivered in 2 weeks with no changes to the UI or database, just the SEO."
    }),
]

v1 = SanskritMeshCompiler()
hc = HyperCompiler(level="hyper")

print(f"{'Payload':<30} {'V1 chars':<10} {'V2 chars':<10} {'V1 %':<8} {'V2 %':<8} {'Lossless':<10}")
print("-" * 80)

for label, payload in payloads:
    orig_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False) if isinstance(payload, dict) else payload
    orig_len = len(orig_str)
    
    v1_comp = v1.compile_payload(payload) if isinstance(payload, dict) else v1.compile_text(payload)
    v1_str = json.dumps(v1_comp, separators=(",", ":"), ensure_ascii=False) if isinstance(payload, dict) else v1_comp
    v1_len = len(v1_str)
    v1_pct = round((1 - v1_len/orig_len) * 100, 1)
    
    v2_comp = hc.compile_payload(payload) if isinstance(payload, dict) else hc.compile_text(payload)
    v2_str = json.dumps(v2_comp, separators=(",", ":"), ensure_ascii=False) if isinstance(payload, dict) else v2_comp
    v2_len = len(v2_str)
    v2_pct = round((1 - v2_len/orig_len) * 100, 1)
    
    restored = hc.decompile_payload(v2_comp) if isinstance(payload, dict) else hc.decompile_text(v2_comp)
    lossless = "PASS" if restored == payload else "FAIL"
    
    print(f"{label:<30} {v1_len:<10} {v2_len:<10} {v1_pct:<8} {v2_pct:<8} {lossless:<10}")