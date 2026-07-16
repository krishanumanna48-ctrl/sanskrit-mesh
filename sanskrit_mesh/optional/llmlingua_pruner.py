import warnings

try:
    import llmlingua
    LLMLINGUA_AVAILABLE = True
except ImportError:
    llmlingua = None
    LLMLINGUA_AVAILABLE = False


class LLMLinguaPruner:
    """
    Lossy entropy-based pruning layer powered by LLMLingua.

    This is an OPT-IN LOSSY path. Text pruned by this layer CANNOT be
    recovered byte-for-byte. Use only when exact reconstruction is not
    required (e.g., compressing freeform human prompts where semantic
    preservation matters more than literal fidelity).

    The reversible entropy layer (L1 in the HyperCompiler) always runs
    first and is lossless. This pruner is a separate, explicit step.
    """

    def __init__(self, enabled: bool = True, model_name="openai-community/gpt2", device="cpu"):
        self.enabled = enabled and LLMLINGUA_AVAILABLE
        self._pruner = None
        if self.enabled:
            try:
                self._pruner = llmlingua.PromptCompressor(model_name=model_name, device=device)
            except Exception as exc:
                warnings.warn(f"LLMLinguaPruner: failed to initialize PromptCompressor: {exc}")
                self.enabled = False

    def prune(self, text: str, rate: float = 0.5, target_token_count: int = None) -> str:
        if not self.enabled:
            return text
        if not isinstance(text, str) or not text.strip():
            return text
        if self._pruner is None:
            return text
        try:
            if target_token_count is not None:
                result = self._pruner.compress_prompt(
                    text,
                    instruction="",
                    question="",
                    target_token=target_token_count,
                )
            else:
                result = self._pruner.compress_prompt(
                    text,
                    instruction="",
                    question="",
                    rate=rate,
                )
            compressed = result.get("compressed_prompt", text)
            return compressed if isinstance(compressed, str) and compressed.strip() else text
        except Exception as exc:
            warnings.warn(f"LLMLinguaPruner: pruning failed, returning original: {exc}")
            return text
