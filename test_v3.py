"""Test V2 properly — compare serialized sizes, verify lossless round-trip."""
import json
from sanskrit_mesh import SanskritMeshCompiler

payloads = [
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
            {"role": "system", "content": "You are a senior AI agent. Always Request Clarification if confused."},
            {"role": "assistant", "content": "The deployment failed. Running again... Task Complete"},
            {"role": "tool", "content": "I encountered the following error: MemoryError: out of memory. Please advise on how to proceed."},
        ]
    }),
    ("Freeform text", {
        "user_message": "I need this app delivered in 2 weeks with no changes to the UI or database, just the SEO."
    }),
]

# Test V1
v1 = SanskritMeshCompiler()
# Test V2 unified compiler
hc_fixed = SanskritMeshCompiler(level="hyper", huffman="fixed")
hc_dyn = SanskritMeshCompiler(level="hyper", huffman="dynamic")

print(f"{'Payload':<30} {'Orig':<8} {'V1':<8} {'V1%':<8} {'V2fix':<8} {'V2fix%':<8} {'V2dyn':<8} {'V2dyn%':<8}")
print("-" * 110)

for label, payload in payloads:
    is_str = isinstance(payload, str)
    orig_str = payload if is_str else json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    orig_len = len(orig_str)
    
    # V1
    v1_comp = v1.compile_payload(payload) if not is_str else v1.compile_text(payload)
    v1_str = json.dumps(v1_comp, separators=(",", ":"), ensure_ascii=False) if not is_str else v1_comp
    v1_len = len(v1_str)
    v1_pct = round((1 - v1_len/orig_len) * 100, 1)
    
    # V2 fixed huffman
    v2f = hc_fixed.compile_payload(payload) if not is_str else hc_fixed.compile_text(payload)
    v2f_str = v2f if isinstance(v2f, str) else json.dumps(v2f, separators=(",", ":"), ensure_ascii=False)
    v2f_len = len(v2f_str)
    v2f_pct = round((1 - v2f_len/orig_len) * 100, 1)
    
    # V2 dynamic huffman
    v2d = hc_dyn.compile_payload(payload) if not is_str else hc_dyn.compile_text(payload)
    v2d_str = v2d if isinstance(v2d, str) else json.dumps(v2d, separators=(",", ":"), ensure_ascii=False)
    v2d_len = len(v2d_str)
    v2d_pct = round((1 - v2d_len/orig_len) * 100, 1)
    
    # Round-trip check
    restored_f = hc_fixed.decompile_payload(v2f) if not is_str else hc_fixed.decompile_text(v2f)
    restored_d = hc_dyn.decompile_payload(v2d) if not is_str else hc_dyn.decompile_text(v2d)
    ok_f = "OK" if restored_f == payload else "FAIL"
    ok_d = "OK" if restored_d == payload else "FAIL"
    
    print(f"{label:<30} {orig_len:<8} {v1_len:<8} {v1_pct:<8} {v2f_len:<8} {v2f_pct:<8} {v2d_len:<8} {v2d_pct:<8}  fix={ok_f} dyn={ok_d}")
    
    if ok_f == "FAIL":
        print(f"  V2 fixed huffman output: {v2f_str[:200]}")
        print(f"  Expected: {orig_str[:100]}")
        print(f"  Got:      {json.dumps(restored_f, separators=(',',':'))[:100]}")