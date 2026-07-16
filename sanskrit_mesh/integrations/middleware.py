import json

from sanskrit_mesh.core.compiler import SanskritMeshCompiler, HyperCompiler
from sanskrit_mesh.core import tables

try:
    from langchain.callbacks.base import BaseCallbackHandler
    LANGCHAIN_AVAILABLE = True
except ImportError:
    BaseCallbackHandler = object
    LANGCHAIN_AVAILABLE = False

try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False


def _make_compiler(level=None, huffman="fixed", entropy_prune=False):
    if level is None or level == tables.LEVEL_V1:
        return SanskritMeshCompiler()
    return HyperCompiler(level=level, huffman=huffman, entropy_prune=entropy_prune)


class SanskritMeshLangChainCallback(BaseCallbackHandler if LANGCHAIN_AVAILABLE else object):
    """Drop-in LangChain callback handler for compressing chat prompts."""

    def __init__(self, verbose: bool = False, level=None, huffman="fixed", entropy_prune=False):
        self.compiler = _make_compiler(level, huffman, entropy_prune)
        self.level = level
        self.verbose = verbose
        self.session_stats = {
            "total_original_chars": 0,
            "total_compressed_chars": 0,
            "calls_intercepted": 0,
        }

    def on_chat_model_start(self, serialized, messages, **kwargs):
        if not LANGCHAIN_AVAILABLE:
            return
        for message_group in messages:
            for msg in message_group:
                if hasattr(msg, "content") and isinstance(msg.content, str):
                    original = msg.content
                    msg.content = self._compile(original)
                    self._track(original, msg.content)
        if self.verbose:
            self._print_stats()

    def on_llm_start(self, serialized, prompts, **kwargs):
        if not LANGCHAIN_AVAILABLE:
            return
        for i, prompt in enumerate(prompts):
            if isinstance(prompt, str):
                original = prompt
                prompts[i] = self._compile(prompt)
                self._track(original, prompts[i])
        if self.verbose:
            self._print_stats()

    def _compile(self, text):
        if self.level is None or self.level == tables.LEVEL_V1:
            return self.compiler.compile_text(text)
        return self.compiler.compile_text(text)

    def _track(self, original: str, compressed: str):
        self.session_stats["total_original_chars"] += len(original)
        self.session_stats["total_compressed_chars"] += len(compressed)
        self.session_stats["calls_intercepted"] += 1

    def _print_stats(self):
        report = self.get_session_report()
        print(
            f"[Sanskrit-Mesh] Intercepted call #{report['calls_intercepted']} | "
            f"Compression: {report['overall_compression_pct']}% | "
            f"Tokens saved this session: ~{report['estimated_tokens_saved']}"
        )

    def get_session_report(self) -> dict:
        total_orig = self.session_stats["total_original_chars"]
        total_comp = self.session_stats["total_compressed_chars"]
        saved = total_orig - total_comp
        pct = round((saved / total_orig) * 100, 2) if total_orig > 0 else 0.0
        return {
            "calls_intercepted": self.session_stats["calls_intercepted"],
            "total_original_chars": total_orig,
            "total_compressed_chars": total_comp,
            "total_chars_saved": saved,
            "overall_compression_pct": pct,
            "estimated_tokens_saved": round(saved / 4),
            "estimated_cost_saved_usd_gpt4o": round((saved / 4 / 1_000_000) * 5, 4),
        }


class SanskritMeshAutoGenHook:
    """Drop-in AutoGen hook for compressing agent messages."""

    def __init__(self, verbose: bool = True, level=None, huffman="fixed", entropy_prune=False):
        self.compiler = _make_compiler(level, huffman, entropy_prune)
        self.level = level
        self.verbose = verbose

    def compress_hook(self, sender, message, recipient, silent):
        compressed = self._compress(message)
        if self.verbose and not silent:
            report = self.compiler.get_savings_report(message, compressed)
            print(
                f"[Sanskrit-Mesh AutoGen] {getattr(sender, 'name', 'Agent')} → "
                f"{getattr(recipient, 'name', 'Agent')} | "
                f"Compression: {report['compression_pct']}% | "
                f"Saved ~{report['estimated_tokens_saved']} tokens"
            )
        return compressed

    def compress_message(self, message):
        return self._compress(message)

    def decompress_message(self, message):
        if isinstance(message, str):
            return self.compiler.decompile_text(message)
        if isinstance(message, dict):
            return self.compiler.decompile_payload(message)
        return message

    def compress_conversation_history(self, history: list) -> list:
        return self.compiler.compile_payload(history)

    def _compress(self, message):
        if isinstance(message, str):
            return self.compiler.compile_text(message)
        if isinstance(message, dict):
            return self.compiler.compile_payload(message)
        return message


class SanskritMeshMiddleware:
    """
    Universal middleware — works with any LLM framework or raw API calls.

    This is the safest integration point if you use OpenAI SDK directly,
    Ollama, LiteLLM, or any other client.

    Usage:
        middleware = SanskritMeshMiddleware()

        compressed_messages = middleware.compress_messages(messages)
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=compressed_messages
        )

        restored = middleware.decompress_text(response.choices[0].message.content)
    """

    def __init__(self, verbose: bool = False, level=None, huffman="fixed", entropy_prune=False):
        self.compiler = _make_compiler(level, huffman, entropy_prune)
        self.level = level
        self.verbose = verbose
        self._session_orig = 0
        self._session_comp = 0

    def compress_messages(self, messages: list) -> list:
        """Compress a list of OpenAI-format message dicts."""
        compressed = []
        for msg in messages:
            if isinstance(msg, dict) and "content" in msg:
                original = msg["content"]
                if isinstance(original, str):
                    comp = self.compiler.compile_text(original)
                    self._track(original, comp)
                    compressed.append({**msg, "content": comp})
                else:
                    compressed.append(msg)
            else:
                compressed.append(msg)

        if self.verbose:
            report = self.get_savings_report()
            print(f"[Sanskrit-Mesh] Compressed {len(messages)} messages | "
                  f"Session savings: {report['overall_compression_pct']}%")
        return compressed

    def decompress_messages(self, messages: list) -> list:
        """Restore a list of compressed message dicts."""
        restored = []
        for msg in messages:
            if isinstance(msg, dict) and "content" in msg:
                if isinstance(msg["content"], str):
                    restored.append({**msg, "content": self.compiler.decompile_text(msg["content"])})
                else:
                    restored.append(msg)
            else:
                restored.append(msg)
        return restored

    def compress_payload(self, payload: dict) -> dict:
        """Compress any arbitrary JSON payload."""
        return self.compiler.compile_payload(payload)

    def decompress_payload(self, payload: dict) -> dict:
        """Restore any compressed JSON payload."""
        return self.compiler.decompile_payload(payload)

    def compress_text(self, text: str) -> str:
        """Compress a plain string."""
        return self.compiler.compile_text(text)

    def decompress_text(self, text: str) -> str:
        """Restore a compressed string."""
        return self.compiler.decompile_text(text)

    def compress_system_prompt(self, prompt: str) -> str:
        """Dedicated system prompt compressor (runs on every API call)."""
        original = prompt
        compressed = self.compiler.compile_system_prompt(prompt)
        self._track(original, compressed)
        if self.verbose:
            report = self.compiler.get_savings_report(original, compressed)
            print(f"[Sanskrit-Mesh] System prompt compressed {report['compression_pct']}%")
        return compressed

    def get_savings_report(self, original=None, compressed=None) -> dict:
        """Get savings report for a specific pair, or session totals if no args given."""
        if original is not None and compressed is not None:
            return self.compiler.get_savings_report(original, compressed)

        saved = self._session_orig - self._session_comp
        pct = round((saved / self._session_orig) * 100, 2) if self._session_orig > 0 else 0.0
        return {
            "overall_compression_pct": pct,
            "total_original_chars": self._session_orig,
            "total_compressed_chars": self._session_comp,
            "total_chars_saved": saved,
            "estimated_tokens_saved": round(saved / 4),
            "estimated_cost_saved_usd_gpt4o": round((saved / 4 / 1_000_000) * 5, 6),
        }

    def _track(self, original: str, compressed: str):
        self._session_orig += len(original)
        self._session_comp += len(compressed)
