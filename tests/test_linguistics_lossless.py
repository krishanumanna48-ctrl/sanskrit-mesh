import unittest

from sanskrit_mesh.core.layers.paninian import PaninianLayer


class LinguisticsLosslessTests(unittest.TestCase):
    def test_sandhi_and_karaka_round_trip(self):
        layer = PaninianLayer(v1_only=False)
        original = "Please review the following information and proceed with the request"
        encoded = layer.encode(original)
        decoded = layer.decode(encoded)
        self.assertEqual(decoded, original)

    def test_phrase_compaction_round_trip(self):
        layer = PaninianLayer(v1_only=False)
        original = "user authentication timestamp and access control management"
        encoded = layer.encode(original)
        decoded = layer.decode(encoded)
        self.assertEqual(decoded, original)

    def test_multilingual_phrase_compaction_round_trip(self):
        layer = PaninianLayer(v1_only=False)
        original = "por favor revise la solicitud"
        encoded = layer.encode(original)
        decoded = layer.decode(encoded)
        self.assertEqual(decoded, original)

    def test_boilerplate_phrase_compaction_round_trip(self):
        layer = PaninianLayer(v1_only=False)
        original = "Please advise on how to proceed."
        encoded = layer.encode(original)
        decoded = layer.decode(encoded)
        self.assertEqual(decoded, original)


if __name__ == "__main__":
    unittest.main()
