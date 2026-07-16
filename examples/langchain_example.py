"""LangChain integration example (no external dependency required).

This script demonstrates using the `SanskritMeshDocumentTransformer` when
`langchain` is available; it falls back to a simple direct call otherwise.
"""
from sanskrit_mesh.integrations.langchain_plugin import SanskritMeshDocumentTransformer
from sanskrit_mesh.core import tables


def main():
    transformer = SanskritMeshDocumentTransformer(level=tables.LEVEL_HYPER, huffman='dynamic')
    sample = "You are a helpful assistant. The deployment failed. Please advise."
    compressed = transformer.transform_text(sample)
    print("Original:", sample)
    print("Compressed:", compressed)


if __name__ == '__main__':
    main()
