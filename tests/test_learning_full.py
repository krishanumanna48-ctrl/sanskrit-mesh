"""End-to-end test: Auto-learning + round-trip lossless verification."""
import json
from sanskrit_mesh.learning import AutoDictionary
from sanskrit_mesh.core.compiler import HyperCompiler

# 1. Create HyperCompiler + AutoDictionary
hc = HyperCompiler(level="hyper")
auto = AutoDictionary(persist_path="test_full_learned.json")

# 2. Simulate repetitive agent traffic (like a real AutoGen pipeline running)
agent_messages = [
    {"sender": "Agent A", "message": "I need to call a tool to deploy the application"},
    {"sender": "Agent B", "message": "The deployment failed due to network error"},
    {"sender": "Agent A", "message": "I need to call a tool to deploy the application"},
    {"sender": "Agent B", "message": "The deployment failed due to network error"},
    {"sender": "Agent A", "message": "I need to call a tool to deploy the application"},
    {"sender": "Agent B", "message": "The deployment failed due to network error"},
]

# 3. Ingest each payload, then learn
for msg in agent_messages:
    auto.ingest(json.dumps(msg))

promoted = auto.learn(top_n=5)
print(f"Auto-learned {len(promoted)} phrases")

# 4. Apply learned dictionary to compiler
auto.apply(hc)
print(f"Dictionary size now: {len(hc._v1_paninian.dictionary)} entries")

# 5. Test round-trip on a payload that contains learned phrases
test_payload = {
    "sender": "Agent A",
    "message": "I need to call a tool to deploy the application and check the deployment failed due to network error"
}

# WITHOUT auto-learning
hc_no_learn = HyperCompiler(level="hyper")
v1_before = hc_no_learn.compile_payload(test_payload)
v1_str = json.dumps(v1_before, separators=(",", ":"), ensure_ascii=False)
print(f"\nBefore learning: {len(v1_str)} chars")

# WITH auto-learning
restored = hc.decompile_payload(hc.compile_payload(test_payload))
v2_str = json.dumps(hc.compile_payload(test_payload), separators=(",", ":"), ensure_ascii=False)
print(f"After learning:  {len(v2_str)} chars")
print(f"Round-trip: {'PASS' if restored == test_payload else 'FAIL'}")

# Show compression impact
orig_str = json.dumps(test_payload, separators=(",", ":"), ensure_ascii=False)
print(f"\nOriginal: {len(orig_str)} chars")
print(f"Before:   {len(v1_str)} chars ({round((1-len(v1_str)/len(orig_str))*100,1)}%)")
print(f"After:    {len(v2_str)} chars ({round((1-len(v2_str)/len(orig_str))*100,1)}%)")
print(f"Improvement: {round(len(v1_str)-len(v2_str),0)} more chars saved")

# Cleanup
import os
if os.path.exists("test_full_learned.json"):
    os.remove("test_full_learned.json")

print("\n✅ Done")