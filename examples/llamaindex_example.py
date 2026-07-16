"""LlamaIndex integration example (safe no-op if dependency missing).

Demonstrates creating a small document and passing it through the transformer.
"""
from sanskrit_mesh.integrations.llamaindex_plugin import SanskritMeshTextTransformer
from sanskrit_mesh.core import tables


def main():
    transformer = SanskritMeshTextTransformer(level=tables.LEVEL_HYPER, huffman="fixed")
    text = "User: How do I reset my password?"
    transformed = transformer.transform(text)
    print("Original:", text)
    print("Transformed:", transformed)

    docs = [
        {"text": "System prompt: You are a helpful assistant. Think step by step."},
        {"text": "The user is requesting a password reset."},
    ]
    transformed_docs = transformer.transform_documents(docs)
    for i, doc in enumerate(transformed_docs):
        print(f"\nDoc {i}: {doc}")


if __name__ == "__main__":
    main()
