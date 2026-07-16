import unittest

from sanskrit_mesh.core.compiler import HyperCompiler


class IRContractTests(unittest.TestCase):
    def test_canonicalize_payload_sorts_nested_keys(self):
        compiler = HyperCompiler(level="hyper", huffman="fixed")
        payload = {"b": 2, "a": {"d": 4, "c": 3}}

        canonical = compiler.canonicalize_payload(payload)

        self.assertEqual(canonical, {"a": {"c": 3, "d": 4}, "b": 2})

    def test_pack_and_unpack_ir_keep_round_trip(self):
        compiler = HyperCompiler(level="hyper", huffman="fixed")
        original = {
            "sender": "Agent A",
            "intent": "Request Clarification",
            "context": {"status": "failed", "message": "Please advise on how to proceed."},
        }

        wrapped = compiler.compile_payload(original, wrap_ir=True, version="2.0.0")
        restored = compiler.decompile_payload(wrapped, unwrap_ir=True)

        self.assertEqual(wrapped["version"], "2.0.0")
        self.assertEqual(wrapped["format"], "json")
        self.assertEqual(restored, original)


if __name__ == "__main__":
    unittest.main()
