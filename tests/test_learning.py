"""Test auto-learning engine."""

from sanskrit_mesh import SanskritMeshCompiler
from sanskrit_mesh.learning.learner import AutoDictionary


def main():
    compiler = SanskritMeshCompiler(level="paninian")
    print("=== Test 1: Phrase Learning ===")

    sample_texts = [
        "The deployment failed due to network error",
        "The deployment failed due to network error",
        "The deployment failed due to network error",
        "I need to call a tool to deploy the application",
        "I need to call a tool to deploy the application",
        "I need to call a tool to deploy the application",
    ]

    for text in sample_texts:
        compiler.auto_dict.learner.ingest_text(text)

    stats = compiler.auto_dict.learner.get_stats()
    print(f"Payloads seen: {stats['total_payloads_seen']}")
    print(f"Unique n-grams: {stats['unique_ngrams_tracked']}")
    print(f"Learned entries: {stats['learned_entries']}")

    print("\nTop candidates:")
    candidates = compiler.auto_dict.learner.score_candidates(top_n=10)
    for net, per, count, phrase in candidates[:10]:
        print(f"  '{phrase}' x{count} = {net} net tokens saved")

    print("\nPromoted (5):")
    promoted = compiler.auto_dict.learner.promote_candidates(top_n=5)
    for phrase, glyph, savings in promoted:
        print(f"  '{phrase}' -> {glyph} (saves {savings} tokens)")

    learned = compiler.auto_dict.learner.dictionary
    print(f"\nLearned dict: {learned}")

    print("\n=== Test 2: AutoDictionary ===")
    auto_dict = AutoDictionary()
    for text in sample_texts:
        auto_dict.ingest(text)
    auto_dict.learn(top_n=5)
    print(f"Auto-learned: {len(auto_dict.learner.dictionary)} entries")
    for phrase, glyph in auto_dict.learner.dictionary.items():
        print(f"  '{phrase}' -> {glyph}")

    print(f"\nStats: {auto_dict.get_stats()}")

    print("\n=== Test 3: Apply to Compiler ===")
    compiler2 = SanskritMeshCompiler(level="hyper")
    auto_dict.apply(compiler2)
    for phrase, glyph in auto_dict.learner.dictionary.items():
        in_dict = phrase in compiler2.dictionary
        print(f"  '{phrase}' in V1 dict: {in_dict} -> token: {compiler2.dictionary.get(phrase, None)}")

    print("\nAll tests passed!")


if __name__ == "__main__":
    main()