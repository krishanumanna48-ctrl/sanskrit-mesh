from sanskrit_mesh.core.compiler import SanskritMeshCompiler, HyperCompiler
from sanskrit_mesh.core import tables

try:
    from langchain.schema import Document
    from langchain.schema import BaseMessage
    from langchain.transformers import BaseDocumentTransformer
    LANGCHAIN_AVAILABLE = True
except ImportError:
    Document = None
    BaseMessage = object
    BaseDocumentTransformer = object
    LANGCHAIN_AVAILABLE = False


def _make_compiler(level=None, huffman="fixed", entropy_prune=False):
    if level is None or level == tables.LEVEL_V1:
        return SanskritMeshCompiler()
    return HyperCompiler(level=level, huffman=huffman, entropy_prune=entropy_prune)


class SanskritMeshDocumentTransformer(BaseDocumentTransformer if LANGCHAIN_AVAILABLE else object):
    """LangChain BaseDocumentTransformer that compresses document text before indexing."""

    def __init__(self, level=None, huffman="fixed", entropy_prune=False):
        self.compiler = _make_compiler(level, huffman, entropy_prune)
        self.level = level

    def transform_documents(self, documents):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("langchain is not installed. Run: pip install langchain")
        transformed = []
        for doc in documents:
            if hasattr(doc, "page_content") and isinstance(doc.page_content, str):
                compressed = self.compiler.compile_text(doc.page_content, level=self.level)
                meta = getattr(doc, "metadata", {})
                try:
                    transformed.append(doc.__class__(page_content=compressed, metadata=meta))
                except Exception:
                    transformed.append(doc)
            else:
                transformed.append(doc)
        return transformed

    def transform_text(self, text):
        return self.compiler.compile_text(text, level=self.level)
