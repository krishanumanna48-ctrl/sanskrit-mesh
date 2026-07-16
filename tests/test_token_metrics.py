import unittest
from sanskrit_mesh.core.token_metrics import TokenMetrics


class TestTokenMetrics(unittest.TestCase):
    def test_report_keys_and_counts(self):
        tm = TokenMetrics(use_exact=False)
        orig = "I encountered an error: TimeoutError: operation timed out."
        comp = "I encountered an error: TO: timeout."
        r = tm.report(orig, comp)
        self.assertIn("original_chars", r)
        self.assertIn("compressed_chars", r)
        self.assertIn("original_tokens", r)
        self.assertIn("compressed_tokens", r)
        self.assertIsInstance(r["original_chars"], int)
        self.assertTrue(r["original_chars"] >= r["compressed_chars"])


if __name__ == "__main__":
    unittest.main()
