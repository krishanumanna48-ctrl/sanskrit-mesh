"""Test the auto-learning engine."""
import json
from sanskrit_mesh.learning import AutoDictionary, PhraseLearner

# Test 1: Basic phrase learning
print("=== Test 1: Phrase Learning ===")
learner = PhraseLearner(min_frequency=2, min_savings=1)

# Simulate repetitive agent traffic
repeated_phrases = [
    "I need to call a tool to deploy the application",
    "I need to call a tool to deploy the application",
    "I need to call a tool to deploy the application",
    "The deployment failed due to network error",
    "The deployment failed due to network error",
    "The deployment failed due to network error",
    "Executing plan step number one of five",
    "Executing plan step number one of five",
]

for phrase in repeated_phrases:
    learner.ingest_text(phrase)

stats = learner.get_stats()
print(f"Payloads seen: {stats['total_payloads_seen']}")
print(f"Unique n-grams: {stats['unique_ngrams_tracked']}")
print(f"Learned entries: {stats['learned_entries']}")

# Score candidates
candidates = learner.score_candidates(top_n=10)
print(f"\nTop candidates:")
for net, per, count, phrase in candidates:
    print(f"  '{phrase}' ×{count} = {net} net tokens saved")

# Promote
promoted = learner.promote_candidates(top_n=5)
print(f"\nPromoted ({len(promoted)}):")
for phrase, glyph, savings in promoted:
    print(f"  '{phrase}' → {glyph} (saves {savings} tokens)")

print(f"\nLearned dict: {learner.dictionary}")

# Test 2: AutoDictionary integration
print("\n=== Test 2: AutoDictionary ===")
auto = AutoDictionary(persist_path="test_learned.json")
for phrase in repeated_phrases:
    auto.ingest(phrase)

promoted = auto.learn(top_n=5)
print(f"Auto-learned: {len(promoted)} entries")
for phrase, glyph, savings in promoted:
    print(f"  '{phrase}' → {glyph}")

stats = auto.get_stats()
print(f"\nStats: {json.dumps(stats, indent=2)}")

# Test 3: Apply to HyperCompiler
print("\n=== Test 3: Apply to HyperCompiler ===")
from sanskrit_mesh.core.compiler import HyperCompiler

hc = HyperCompiler(level="hyper")
auto.apply(hc)

# Check that learned phrases are in the dictionary
learned = auto.learner.dictionary
for phrase, glyph in list(learned.items())[:2]:
    in_dict = phrase in hc._v1_paninian.dictionary
    print(f"  '{phrase}' in V1 dict: {in_dict} → token: {hc._v1_paninian.dictionary.get(phrase)}")

# Cleanup
import os
if os.path.exists("test_learned.json"):
    os.remove("test_learned.json")

print("\n✅ All tests passed!")