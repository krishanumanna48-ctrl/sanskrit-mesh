from sanskrit_mesh.core.compiler import SanskritMeshCompiler

__version__ = "2.0.0"
__all__ = ["SanskritMeshCompiler", "__version__"]

# Backward compat: HyperCompiler is now SanskritMeshCompiler(level="hyper")
import warnings
class HyperCompiler:
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "HyperCompiler is deprecated. Use SanskritMeshCompiler(level='hyper') instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._compiler = SanskritMeshCompiler(*args, **kwargs)
    
    def __getattr__(self, name):
        return getattr(self._compiler, name)
