import json
import os
import unittest

from sanskrit_mesh.core.compiler import HyperCompiler
from sanskrit_mesh.core import tables
from sanskrit_mesh.core.registry import DynamicRegistry


class TestCoreLayers(unittest.TestCase):
    def test_entropy_roundtrip(self):
        hc = HyperCompiler(level=tables.LEVEL_ENTROPY)
        text = "The agent reported an error: NullPointerException: object reference not set."
        enc = hc.compile_text(text)
        dec = hc.decompile_text(enc)
        self.assertEqual(text, dec)

    def test_structural_roundtrip(self):
        hc = HyperCompiler(level=tables.LEVEL_STRUCTURAL)
        payload = {
            "sender": "Agent A",
            "intent": "Formulating Plan",
            "context": {"status": "running", "notes": "Step 1 completed."},
        }
        enc = hc.compile_payload(payload)
        dec = hc.decompile_payload(enc)
        self.assertEqual(payload, dec)

    def test_huffman_fixed_and_dynamic(self):
        payload = {
            "message": "I encountered the following error: TimeoutError: operation timed out. Please advise."
        }
        # fixed
        hc_fixed = HyperCompiler(level=tables.LEVEL_HYPER, huffman="fixed")
        enc_fixed = hc_fixed.compile_payload(payload)
        dec_fixed = hc_fixed.decompile_payload(enc_fixed)
        self.assertEqual(payload, dec_fixed)
        # dynamic
        hc_dyn = HyperCompiler(level=tables.LEVEL_HYPER, huffman="dynamic")
        enc_dyn = hc_dyn.compile_payload(payload)
        dec_dyn = hc_dyn.decompile_payload(enc_dyn)
        self.assertEqual(payload, dec_dyn)

    def test_registry_persist_and_collision(self):
        reg = DynamicRegistry()
        a = reg.get_or_assign("alpha")
        b = reg.get_or_assign("beta")
        tmp = os.path.join(os.getcwd(), "tmp_reg.json")
        try:
            reg.persist(tmp)
            r2 = DynamicRegistry()
            r2.restore(tmp)
            self.assertEqual(r2.lookup(a), "alpha")
            # simulate collision
            r3 = DynamicRegistry()
            r3.load({"gamma": a})
            r3.load({"alpha": a})
            # both keys should exist, markers may differ
            self.assertIn("gamma", r3.dump())
            self.assertIn("alpha", r3.dump())
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def test_paninian_sandhi_roundtrip(self):
        # Use full paninian (not v1-only) to exercise sandhi handling
        from sanskrit_mesh.core.compiler import HyperCompiler
        hc = HyperCompiler(level=tables.LEVEL_PANINIAN)
        text = "I am a agent A"  # 'a agent' creates vowel-vowel boundary (a <space> a)
        enc = hc.compile_text(text)
        dec = hc.decompile_text(enc)
        self.assertEqual(text, dec)


if __name__ == "__main__":
    unittest.main()
