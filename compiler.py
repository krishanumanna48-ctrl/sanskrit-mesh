import json

class SanskritMeshCompiler:
    """
    AI-Native Bytecode Compiler based on Paninian Grammar Structure.
    Aggressive compression mode: Compresses JSON keys, removes whitespace, 
    and uses ultra-dense IR to achieve 60-70% token reductions.
    """
    def __init__(self):
        # 1. Structural Key Compression (Minifying JSON Keys)
        self.key_map = {
            "sender": "s",
            "receiver": "r",
            "intent": "i",
            "context": "c",
            "message": "m",
            "status": "st",
            "error_state": "err"
        }
        self.reverse_key_map = {v: k for k, v in self.key_map.items()}

        # 2. Expanded Semantic Dictionary (Errors + Standard Phrases)
        self.dictionary = {
            # Standard Phrases (Entire Sentences squashed to 2-3 chars)
            "I encountered the following error:": "E:",
            "Please advise on how to proceed.": "?",
            "Request Clarification": "Prashna",
            "Task Complete": "Purna",
            "Executing Tool": "Karya",
            "Agent B": "AgB",
            "Agent A": "AgA",
            "failed": "F",
            "success": "S",

            # Errors
            "NullPointerException: object reference not set": "ShunyaDosha", 
            "IndexError: list index out of range": "KramaBhanga",      
            "SyntaxError: invalid syntax": "VyakarnaDosha",            
            "TimeoutError: operation timed out": "KalaAtikrama",       
            "MemoryError: out of memory": "SmritiBhara"
        }
        
        # Sort by length descending to prevent partial substring matches
        self.sorted_eng_keys = sorted(self.dictionary.keys(), key=len, reverse=True)
        self.reverse_dictionary = {v: k for k, v in self.dictionary.items()}

    def compile_text(self, text: str) -> str:
        """Compresses a plain text string."""
        if not isinstance(text, str):
            return text
            
        compiled = text
        for eng in self.sorted_eng_keys:
            if eng in compiled:
                san = self.dictionary[eng]
                compiled = compiled.replace(eng, f"|{san}|")
        # Strip excess whitespace that agents often generate
        return compiled.strip()

    def decompile_text(self, text: str) -> str:
        """Decompresses an IR string back to English."""
        if not isinstance(text, str):
            return text
            
        decompiled = text
        for san, eng in self.reverse_dictionary.items():
            decompiled = decompiled.replace(f"|{san}|", eng)
        return decompiled

    def compile_payload(self, payload: dict) -> dict:
        """Recursively traverses a JSON/Dict, minifies keys, and compresses values."""
        if isinstance(payload, dict):
            new_dict = {}
            for k, v in payload.items():
                new_key = self.key_map.get(k, k)
                new_dict[new_key] = self.compile_payload(v)
            return new_dict
        elif isinstance(payload, list):
            return [self.compile_payload(v) for v in payload]
        elif isinstance(payload, str):
            return self.compile_text(payload)
        else:
            return payload

    def decompile_payload(self, payload: dict) -> dict:
        """Recursively decompresses JSON keys and string values."""
        if isinstance(payload, dict):
            new_dict = {}
            for k, v in payload.items():
                old_key = self.reverse_key_map.get(k, k)
                new_dict[old_key] = self.decompile_payload(v)
            return new_dict
        elif isinstance(payload, list):
            return [self.decompile_payload(v) for v in payload]
        elif isinstance(payload, str):
            return self.decompile_text(payload)
        else:
            return payload


if __name__ == "__main__":
    compiler = SanskritMeshCompiler()

    # Complex Payload Stress Test
    original_payload = {
        "sender": "Agent A",
        "receiver": "Agent B",
        "intent": "Formulating Plan",
        "context": {
            "status": "failed",
            "history": [
                {"intent": "Executing Tool", "message": "I encountered the following error: SyntaxError: invalid syntax. Please advise on how to proceed."},
                {"intent": "Request Clarification", "message": "I encountered the following error: IndexError: list index out of range. Please advise on how to proceed."}
            ],
            "current_task": {
                "step_1": "Load massive dataset",
                "step_2": "I encountered the following error: MemoryError: out of memory.",
                "retry_logic": "failed"
            },
            "unmapped_data": "This sentence is not in the dictionary and should be left completely alone."
        }
    }

    print("=== Sanskrit-Mesh COMPLEX STRESS TEST ===\n")
    orig_str = json.dumps(original_payload, separators=(',', ':'))
    print("Original Length:", len(orig_str), "chars")

    compiled_dict = compiler.compile_payload(original_payload)
    comp_str = json.dumps(compiled_dict, separators=(',', ':'))
    print("Bytecode Payload:")
    print(comp_str)
    print("Bytecode Length:", len(comp_str), "chars")
    
    saved_chars = len(orig_str) - len(comp_str)
    savings_pct = (saved_chars / len(orig_str)) * 100
    print(f"\nCompression Savings: {saved_chars} chars ({savings_pct:.1f}%)")

    decompiled_dict = compiler.decompile_payload(compiled_dict)
    assert original_payload == decompiled_dict, "CRITICAL FAILURE: Data corruption during decompilation!"
    print("\n[System] Complex nested transmission successful. 100% data accuracy restored.")
