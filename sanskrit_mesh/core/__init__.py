from .compiler import SanskritMeshCompiler
from .registry import DynamicRegistry
from .token_metrics import TokenMetrics
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

__all__ = ["SanskritMeshCompiler", "HyperCompiler", "DynamicRegistry", "TokenMetrics"]
