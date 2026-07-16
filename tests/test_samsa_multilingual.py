import unittest

from sanskrit_mesh.core import tables
from sanskrit_mesh.core.compiler import SanskritMeshCompiler
from sanskrit_mesh.core.layers.paninian import PaninianLayer


class SamasaAndMultilingualTests(unittest.TestCase):
    def test_samsa_phrase_round_trip(self):
        layer = PaninianLayer(v1_only=False)
        original = "request clarification"
        encoded = layer.encode(original)
        decoded = layer.decode(encoded)
        self.assertEqual(decoded, original)

    def test_multilingual_phrase_round_trip(self):
        layer = PaninianLayer(v1_only=False)
        original = "por favor revise la solicitud"
        encoded = layer.encode(original)
        decoded = layer.decode(encoded)
        self.assertEqual(decoded, original)

    def test_agent_domain_phrase_replacement_is_shorter_and_round_trip(self):
        layer = PaninianLayer(v1_only=False)
        original = "deployment failure"
        encoded = layer.encode(original)
        decoded = layer.decode(encoded)
        self.assertEqual(decoded, original)
        self.assertIn("NiyojanaDosha", encoded)
        self.assertLess(len(encoded), len(original))

    def test_realistic_agent_payload_hits_domain_savings_target(self):
        compiler = SanskritMeshCompiler()
        payload = {
            "agent_scratchpad": (
                "Thought: I need to inspect the repository first. "
                "I will list the relevant files and inspect the current implementation. "
                "Action: read_file. Action Input: config.yaml. "
                "Observation: The file exists and contains the deployment settings. "
                "Thought: The settings look correct. I should verify the package version and dependencies. "
                "Action: read_file. Action Input: requirements.txt. "
                "Observation: The dependency list is valid. Thought: I need to run the tests next. "
                "Action: run_tests. Action Input: pytest -q. "
                "Observation: The tests failed because of a missing environment variable. "
                "Thought: I should request clarification before continuing. "
                "Final Answer: I need clarification before I can continue safely."
            ),
            "history": [
                {
                    "role": "system",
                    "content": "You are an autonomous coding agent. Use tools to inspect files and run tests. Always request clarification when the task is ambiguous.",
                },
                {
                    "role": "user",
                    "content": "Please inspect the repository and determine why the deployment failed.",
                },
                {
                    "role": "assistant",
                    "content": "I will inspect the deployment config, the package manifests, and the latest error logs.",
                },
                {
                    "role": "tool",
                    "name": "ReadFile",
                    "content": "The deployment config references a missing secret and a stale image tag.",
                },
                {
                    "role": "assistant",
                    "content": "The deployment appears to be failing because the environment is missing a required secret and the image tag is outdated.",
                },
            ],
        }
        encoded = compiler.compile_payload(payload, level=tables.LEVEL_HYPER)
        restored = compiler.decompile_payload(encoded, level=tables.LEVEL_HYPER)
        self.assertEqual(restored, payload)

        original_text = str(payload)
        encoded_text = str(encoded)
        pct = ((len(original_text) - len(encoded_text)) / len(original_text)) * 100
        self.assertGreaterEqual(pct, 15.0)


if __name__ == "__main__":
    unittest.main()
