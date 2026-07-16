try:
    from .llmlingua_pruner import LLMLinguaPruner
    LINGUA_AVAILABLE = True
except Exception:
    LLMLinguaPruner = None
    LINGUA_AVAILABLE = False

__all__ = ["LLMLinguaPruner", "LINGUA_AVAILABLE"]
