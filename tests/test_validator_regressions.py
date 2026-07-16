import unittest

from validator import validate


class ValidatorRegressionTests(unittest.TestCase):
    def test_linguistic_phrase_payload_round_trip(self):
        payload = {
            "message": "Please review the following information and proceed with the request",
            "metadata": {"context": "user authentication timestamp and access control management"},
        }
        self.assertTrue(validate(payload, label="linguistic regression", level="hyper"))

    def test_nested_payload_with_unicode_round_trip(self):
        payload = {
            "text": "नमस्ते, this is a test with emoji 😀 and punctuation.",
            "steps": [{"note": "Please review the following information"}],
        }
        self.assertTrue(validate(payload, label="unicode regression", level="hyper"))


if __name__ == "__main__":
    unittest.main()
