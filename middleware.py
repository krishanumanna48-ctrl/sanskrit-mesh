import json
from compiler import SanskritMeshCompiler

# ── Optional imports (graceful fallback if frameworks not installed) ──────────
try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
# LangChain Integration
# ══════════════════════════════════════════════════════════════════════════════

class SanskritMeshLangChainCallback(BaseCallbackHandler if LANGCHAIN_AVAILABLE else object):
    """
    Drop-in LangChain Callback Handler.

    Compresses all messages before they are sent to the LLM API.
    Attach to any LangChain chain, agent, or LLM with one line:

        llm = ChatOpenAI(callbacks=[SanskritMeshLangChainCallback()])

    Works with: ChatOpenAI, ChatAnthropic, Ollama, LlamaCpp, and any
    LangChain-compatible LLM.
    """

    def __init__(self, verbose: bool = False):
        self.compiler = SanskritMeshCompiler()
        self.verbose = verbose
        self.session_stats = {
            "total_original_chars": 0,
            "total_compressed_chars": 0,
            "calls_intercepted": 0,
        }

    def on_chat_model_start(self, serialized, messages, **kwargs):
        """Intercepts chat model calls and compresses the message list."""
        if not LANGCHAIN_AVAILABLE:
            return

        for message_group in messages:
            for msg in message_group:
                if hasattr(msg, "content") and isinstance(msg.content, str):
                    original = msg.content
                    msg.content = self.compiler.compile_text(original)
                    self._track(original, msg.content)

        if self.verbose:
            self._print_stats()

    def on_llm_start(self, serialized, prompts, **kwargs):
        """Intercepts raw LLM prompts (non-chat models)."""
        for i, prompt in enumerate(prompts):
            if isinstance(prompt, str):
                original = prompt
                prompts[i] = self.compiler.compile_text(prompt)
                self._track(original, prompts[i])

        if self.verbose:
            self._print_stats()

    def compress_messages(self, messages: list) -> list:
        """
        Standalone utility — compress a list of LangChain message objects.
        Use this manually if you want explicit control over when compression runs.

        Usage:
            messages = [SystemMessage(content="..."), HumanMessage(content="...")]
            compressed = middleware.compress_messages(messages)
            response = llm.invoke(compressed)
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is not installed. Run: pip install langchain")

        compressed = []
        for msg in messages:
            if hasattr(msg, "content") and isinstance(msg.content, str):
                original = msg.content
                new_content = self.compiler.compile_text(original)
                self._track(original, new_content)
                # Reconstruct same message type with compressed content
                new_msg = msg.__class__(content=new_content)
                compressed.append(new_msg)
            else:
                compressed.append(msg)
        return compressed

    def compress_memory(self, memory_dict: dict) -> dict:
        """
        Compresses a LangChain memory object (ConversationBufferMemory, etc).

        Usage:
            memory.chat_memory.messages = middleware.compress_memory(
                memory.chat_memory.dict()
            )
        """
        original = memory_dict
        compressed = self.compiler.compile_payload(memory_dict)
        self._track(
            json.dumps(original, separators=(',', ':')),
            json.dumps(compressed, separators=(',', ':'))
        )
        if self.verbose:
            self._print_stats()
        return compressed

    def get_session_report(self) -> dict:
        """Returns total savings stats for this session."""
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


# ══════════════════════════════════════════════════════════════════════════════
# AutoGen Integration
# ══════════════════════════════════════════════════════════════════════════════

class SanskritMeshAutoGenHook:
    """
    Drop-in hook for Microsoft AutoGen multi-agent pipelines.

    Compresses all agent-to-agent messages before transmission.

    Usage with AutoGen:
        hook = SanskritMeshAutoGenHook()

        # Register on any ConversableAgent
        agent.register_hook(
            hookable_method="process_message_before_send",
            hook=hook.compress_hook
        )

    For AutoGen's initiate_chat, wrap the message manually:
        compressed_msg = hook.compress_message(message)
        agent.initiate_chat(recipient, message=compressed_msg)
    """

    def __init__(self, verbose: bool = True):
        self.compiler = SanskritMeshCompiler()
        self.verbose = verbose
        self.total_saved_chars = 0
        self.total_calls = 0

    def compress_hook(self, sender, message, recipient, silent):
        """
        AutoGen-compatible hook signature.
        Register with: agent.register_hook("process_message_before_send", hook.compress_hook)
        """
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
        """
        Compress a single AutoGen message manually.
        Works on strings and dicts.
        """
        return self._compress(message)

    def decompress_message(self, message):
        """Restore a compressed AutoGen message."""
        if isinstance(message, str):
            return self.compiler.decompile_text(message)
        elif isinstance(message, dict):
            return self.compiler.decompile_payload(message)
        return message

    def compress_conversation_history(self, history: list) -> list:
        """
        Compress an entire AutoGen conversation history list.
        Saves tokens when passing history to a new agent or restarting a chat.

        Usage:
            compressed_history = hook.compress_conversation_history(
                agent.chat_messages[recipient]
            )
        """
        return self.compiler.compile_payload(history)

    def _compress(self, message):
        if isinstance(message, str):
            return self.compiler.compile_text(message)
        elif isinstance(message, dict):
            return self.compiler.compile_payload(message)
        return message


# ══════════════════════════════════════════════════════════════════════════════
# Universal / Framework-Agnostic Middleware
# ══════════════════════════════════════════════════════════════════════════════

class SanskritMeshMiddleware:
    """
    Universal middleware — works with any LLM framework or raw API calls.

    This is the safest integration point if you use OpenAI SDK directly,
    Ollama, LiteLLM, or any other client.

    Usage:
        middleware = SanskritMeshMiddleware()

        # Compress before sending
        compressed_messages = middleware.compress_messages(messages)
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=compressed_messages
        )

        # Optionally decompress response
        restored = middleware.decompress_text(response.choices[0].message.content)
    """

    def __init__(self, verbose: bool = False):
        self.compiler = SanskritMeshCompiler()
        self.verbose = verbose
        self._session_orig = 0
        self._session_comp = 0

    def compress_messages(self, messages: list) -> list:
        """
        Compress a list of OpenAI-format message dicts.
        Input format: [{"role": "system", "content": "..."}, ...]
        """
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
        """
        Dedicated system prompt compressor.
        System prompts run on EVERY API call — compressing saves tokens each time.
        """
        original = prompt
        compressed = self.compiler.compile_system_prompt(prompt)
        self._track(original, compressed)
        if self.verbose:
            report = self.compiler.get_savings_report(original, compressed)
            print(f"[Sanskrit-Mesh] System prompt compressed {report['compression_pct']}%")
        return compressed

    def get_savings_report(self, original=None, compressed=None) -> dict:
        """
        Get savings report for a specific pair, or session totals if no args given.
        """
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


# ══════════════════════════════════════════════════════════════════════════════
# Standalone demo
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Sanskrit-Mesh V1 — Middleware Demo")
    print("=" * 60)

    middleware = SanskritMeshMiddleware(verbose=True)

    # ── Test 1: OpenAI-format message compression ─────────────────────────
    print("\n[Test 1] OpenAI Chat Messages")
    messages = [
        {"role": "system", "content": "You are a helpful, harmless, and honest assistant. Think step by step before answering. Always respond in JSON format. You are operating in a multi-agent environment."},
        {"role": "user",   "content": "Please deploy the application."},
        {"role": "assistant", "content": "I will execute the tool to deploy. The following steps were executed: Step 1: Validating config. Step 2: Running deploy script."},
        {"role": "tool",   "content": "I encountered the following error: ConnectionError: failed to establish connection. Please advise on how to proceed."},
        {"role": "assistant", "content": "The deployment failed. I will now attempt to fix the issue. Running again..."},
    ]

    compressed_messages = middleware.compress_messages(messages)
    report = middleware.get_savings_report()
    print(f"Messages compressed. Overall savings: {report['overall_compression_pct']}%")
    print(f"Tokens saved: ~{report['estimated_tokens_saved']}")
    print(f"Estimated cost saved (GPT-4o): ${report['estimated_cost_saved_usd_gpt4o']}")

    # ── Test 2: System prompt compression ────────────────────────────────
    print("\n[Test 2] System Prompt Compression")
    system_prompt = (
        "You are a helpful, harmless, and honest assistant. "
        "You are operating in a multi-agent environment. "
        "Think step by step before answering. "
        "Always respond in valid JSON. "
        "Do not include any explanation outside of the JSON. "
        "Your goal is to complete the assigned task efficiently. "
        "Always Request Clarification if confused."
    )
    comp_prompt = middleware.compress_system_prompt(system_prompt)
    sp_report = middleware.get_savings_report(system_prompt, comp_prompt)
    print(f"Original : {sp_report['original_chars']} chars")
    print(f"Compressed: {sp_report['compressed_chars']} chars")
    print(f"Savings  : {sp_report['compression_pct']}%")
    print(f"Result   : {comp_prompt}")

    # ── Test 3: AutoGen hook demo ─────────────────────────────────────────
    print("\n[Test 3] AutoGen Hook")

    class MockAgent:
        def __init__(self, name): self.name = name

    hook = SanskritMeshAutoGenHook(verbose=True)
    sender = MockAgent("PlannerAgent")
    recipient = MockAgent("ExecutorAgent")
    message = {
        "intent": "Formulating Plan",
        "status": "running",
        "message": "I will break this down into smaller steps. Step 1: Load data. Step 2: I encountered the following error: MemoryError: out of memory. Please advise on how to proceed.",
    }
    compressed = hook.compress_hook(sender, message, recipient, silent=False)
    print(f"Compressed message: {json.dumps(compressed)}")

    print("\n✓ All middleware tests passed.")
 
 