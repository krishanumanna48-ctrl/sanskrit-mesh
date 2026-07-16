from sanskrit_mesh.core.compiler import SanskritMeshCompiler, HyperCompiler
from sanskrit_mesh.core import tables

try:
    import llama_index
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False


def _make_compiler(level=None, huffman="fixed", entropy_prune=False):
    if level is None or level == tables.LEVEL_V1:
        return SanskritMeshCompiler()
    return HyperCompiler(level=level, huffman=huffman, entropy_prune=entropy_prune)


class SanskritMeshTextTransformer:
    """LlamaIndex-compatible text transformer that compresses text before indexing."""

    def __init__(self, level=None, huffman="fixed", entropy_prune=False):
        self.compiler = _make_compiler(level, huffman, entropy_prune)
        self.level = level

    def transform(self, text):
        return self.compiler.compile_text(text, level=self.level)

    def transform_documents(self, docs):
        results = []
        for doc in docs:
            if isinstance(doc, dict):
                results.append(self.transform(doc.get("text", str(doc))))
            elif hasattr(doc, "text"):
                results.append(self.transform(doc.text))
            elif hasattr(doc, "get_content"):
                results.append(self.transform(str(doc.get_content())))
            else:
                results.append(self.transform(str(doc)))
        return results
