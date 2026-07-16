from sanskrit_mesh import SanskritMeshCompiler

compiler = SanskritMeshCompiler(level="hyper", huffman="fixed")

payload = {
    "sender": "Agent A",
    "receiver": "Agent B",
    "intent": "Request Clarification",
    "context": {"status": "failed", "message": "I encountered the following error: NullPointerException: object reference not set. Please advise on how to proceed."}
}

compressed = compiler.compile_payload(payload)
print("Compressed:", compressed)

decompressed = compiler.decompile_payload(compressed)
print("Decompressed:", decompressed)

print("Equal:", decompressed == payload)
if decompressed != payload:
    import json
    print("Original JSON:", json.dumps(payload, indent=2))
    print("Got JSON:", json.dumps(decompressed, indent=2))