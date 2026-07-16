__all__ = []

# Import integration entrypoints lazily and defensively so test discovery
# doesn't fail when optional dependencies are absent or names are missing.
try:
    from .middleware import SanskritMeshLangChainCallback, SanskritMeshAutoGenHook
    __all__.extend(["SanskritMeshLangChainCallback", "SanskritMeshAutoGenHook"])
except Exception:
    pass

try:
    from .langchain_plugin import SanskritMeshDocumentTransformer
    __all__.append("SanskritMeshDocumentTransformer")
except Exception:
    pass

try:
    from .llamaindex_plugin import SanskritMeshTextTransformer
    __all__.append("SanskritMeshTextTransformer")
except Exception:
    pass

try:
    from .autogen_plugin import SanskritMeshAutoGenHook as AutoGenPlugin
    __all__.append("AutoGenPlugin")
except Exception:
    pass
