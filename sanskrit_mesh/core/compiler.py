import json

from sanskrit_mesh.core import tables
from sanskrit_mesh.core.token_metrics import TokenMetrics
from sanskrit_mesh.core.registry import DynamicRegistry
from sanskrit_mesh.core.layers.paninian import PaninianLayer
from sanskrit_mesh.core.layers.entropy import EntropyLayer
from sanskrit_mesh.core.layers.structural import StructuralLayer
from sanskrit_mesh.core.layers.huffman import HuffmanLayer
from sanskrit_mesh.core.layers.numeric import encode_numerics, decode_numerics, is_numeric_heavy
from sanskrit_mesh.learning.learner import AutoDictionary


class SanskritMeshCompiler:
    """
    Sanskrit-Mesh V2 — Unified Compiler.
    
    Default behaviour is byte-identical to v1. Pass level= to access v2 layers.
    Auto-learning is default-on when level != "v1".
    """

    def __init__(self, level=tables.LEVEL_V1, huffman="fixed", enable_auto_learning=True):
        self.level = level if level in tables.LEVEL_ORDER else tables.LEVEL_V1
        self.huffman_mode = huffman
        self.enable_auto_learning = enable_auto_learning
        
        # V1 baseline structures (always present for backward compat)
        self.key_map = dict(tables.V1_KEY_MAP)
        self.reverse_key_map = {v: k for k, v in self.key_map.items()}
        self.dictionary = dict(tables.V1_DICTIONARY)
        self.sorted_eng_keys = sorted(self.dictionary.keys(), key=len, reverse=True)
        self.reverse_dictionary = {v: k for k, v in self.dictionary.items()}
        self._paninian_v1 = PaninianLayer(v1_only=True)
        
        # V2 structures (lazy init for V1 to keep zero overhead)
        self._v2_initialized = False
        self._paninian_full = None
        self.entropy = None
        self.structural = None
        self.huffman = None
        self.registry = None
        self.metrics = TokenMetrics()
        
        # Auto-learning
        self.auto_dict = AutoDictionary(persist_path="learned_dict.json") if enable_auto_learning else None
        
        if self.level != tables.LEVEL_V1:
            self._init_v2()

    def _init_v2(self):
        """Initialize V2 layers only when needed."""
        if self._v2_initialized:
            return
        self.registry = DynamicRegistry()
        self.entropy = EntropyLayer()
        self.structural = StructuralLayer(registry=self.registry)
        self._paninian_full = PaninianLayer(v1_only=False)
        self.huffman = HuffmanLayer(mode=self.huffman_mode)
        self._v2_initialized = True
        
        # Restore learned dictionary
        if self.auto_dict:
            self.auto_dict.apply(self)

    def _paninian_for_level(self):
        if self.level == tables.LEVEL_V1:
            return self._paninian_v1
        if self._paninian_full:
            return self._paninian_full
        return self._paninian_v1

    def _layers_active(self):
        level = self.level
        # SAFE DEFAULT: entropy and huffman are opt-in only due to token collision risk
        # Proven lossless stack: paninian + structural + auto-learning
        return {
            "entropy": level == tables.LEVEL_ENTROPY,
            "structural": level in (tables.LEVEL_STRUCTURAL, tables.LEVEL_HYPER, tables.LEVEL_PANINIAN),
            "paninian": True,
            "huffman": level == tables.LEVEL_HYPER and self.huffman_mode != "off",
        }

    def compile_text(self, text, level=None):
        target_level = level if level else self.level
        if target_level == tables.LEVEL_V1 or target_level is None:
            return self._compile_text_v1(text)
        return self._compile_text_v2(text)

    def _compile_text_v1(self, text):
        if not isinstance(text, str):
            return text
        return self._paninian_v1.compile_text(text)

    def decompile_text(self, text, level=None):
        target_level = level if level else self.level
        if target_level == tables.LEVEL_V1 or target_level is None:
            return self._decompile_text_v1(text)
        return self._decompile_text_v2(text)

    def _decompile_text_v1(self, text):
        if not isinstance(text, str):
            return text
        return self._paninian_v1.decompile_text(text)

    def compile_payload(self, payload, level=None):
        target_level = level if level else self.level
        if target_level == tables.LEVEL_V1 or target_level is None:
            return self._compile_payload_v1(payload)
        return self._compile_payload_v2(payload)

    def _compile_payload_v1(self, payload):
        if isinstance(payload, dict):
            return {
                self.key_map.get(k, k): self._compile_payload_v1(v)
                for k, v in payload.items()
            }
        elif isinstance(payload, list):
            return [self._compile_payload_v1(item) for item in payload]
        elif isinstance(payload, str):
            return self._compile_text_v1(payload)
        return payload

    def decompile_payload(self, payload, level=None):
        target_level = level if level else self.level
        if target_level == tables.LEVEL_V1 or target_level is None:
            return self._decompile_payload_v1(payload)
        return self._decompile_payload_v2(payload)

    def _decompile_payload_v1(self, payload):
        if isinstance(payload, dict):
            return {
                self.reverse_key_map.get(k, k): self._decompile_payload_v1(v)
                for k, v in payload.items()
            }
        elif isinstance(payload, list):
            return [self._decompile_payload_v1(item) for item in payload]
        elif isinstance(payload, str):
            return self._decompile_text_v1(payload)
        return payload

    def _compile_text_v2(self, text):
        if not self._v2_initialized:
            self._init_v2()
        if not isinstance(text, str):
            return text
        active = self._layers_active()
        result = text
        # CORRECT ORDER: paninian first (longest matches), then agglutination+enum, then entropy
        result = self._paninian_for_level().encode(result)
        if active["structural"]:
            result = self.structural.encode_text_with_enums(result)
        if active["entropy"]:
            result = self.entropy.encode(result)
        # Numeric compression disabled by default (opt-in only)
        if active["huffman"]:
            result = self.huffman.encode(result)
        return result

    def _decompile_text_v2(self, text):
        if not isinstance(text, str):
            return text
        if not self._v2_initialized:
            self._init_v2()
        active = self._layers_active()
        result = text
        if active["huffman"]:
            body, envelope = self.huffman.strip_envelope(result)
            result = self.huffman.decode(body, envelope)
        if active["entropy"]:
            result = self.entropy.decode(result)
        if active["structural"]:
            result = self.structural.decode_text_with_enums(result)
        result = self._paninian_for_level().decode(result)
        return result

    def _compile_payload_v2(self, payload, wrap_ir=False, version="2.0.0"):
        """V2 full-stack: entropy -> structural -> paninian -> huffman."""
        if not self._v2_initialized:
            self._init_v2()
        canonical = self.canonicalize_payload(payload)
        if isinstance(canonical, dict):
            return self._encode_payload_full(canonical, wrap_ir=wrap_ir, version=version)
        elif isinstance(canonical, list):
            wrapped = [self._compile_payload_v2(item, wrap_ir=False, version=version) for item in canonical]
            if wrap_ir:
                return {"version": version, "format": "json", "layers": ["v2-full"], "payload": wrapped}
            return wrapped
        elif isinstance(canonical, str):
            return self._compile_text_v2(canonical)
        return canonical

    def _encode_payload_full(self, payload, wrap_ir=False, version="2.0.0"):
        """Full encoding pipeline: text compression first, then key minification."""
        # Step 1: Text layers (paninian -> agglutination -> entropy + numeric)
        text_compressed = self._apply_text_layers_123(payload)
        # Step 2: Key minification only (no B-H value transforms — those are unsafe)
        key_minified = self.structural.encode_keys_only(text_compressed)
        # Step 3: Registry embedding
        registry_data = self.registry.dump() if self.registry else None
        if registry_data:
            if isinstance(key_minified, dict):
                key_minified[tables.REGISTRY_KEY] = registry_data
            else:
                key_minified = {tables.REGISTRY_KEY: registry_data, "payload": key_minified}
        return key_minified

    def _apply_text_layers_123(self, payload):
        """Apply paninian -> agglutination+enum to string values.
        
        Entropy and numeric compression are opt-in only due to collision risk.
        """
        if isinstance(payload, dict):
            return {k: self._apply_text_layers_123(v) for k, v in payload.items()}
        elif isinstance(payload, list):
            return [self._apply_text_layers_123(item) for item in payload]
        elif isinstance(payload, str):
            if not payload:
                return payload
            result = payload
            active = self._layers_active()
            # CORRECT ORDER: paninian first, then agglutination+enum
            result = self._paninian_for_level().encode(result)
            if active["structural"]:
                result = self.structural.encode_text_with_enums(result)
            # Entropy is skipped unless explicitly opt-in (level="entropy")
            if active["entropy"] and '|' not in result:
                result = self.entropy.encode(result)
            # Numeric compression disabled by default (corrupts dates/uuids)
            # Enable with level="numeric" or by calling encode_numerics manually
            return result
        return payload

    def canonicalize_payload(self, payload):
        if isinstance(payload, dict):
            return {k: self.canonicalize_payload(payload[k]) for k in sorted(payload)}
        if isinstance(payload, list):
            return [self.canonicalize_payload(item) for item in payload]
        return payload

    def _decompile_payload_v2(self, payload, unwrap_ir=False):
        """Full decode: inverse of _encode_payload_full.
        
        Correct inverse order:
          1. Huffman decode (if present)
          2. Entropy decode
          3. Numeric decode
          4. Text layer decode (paninian -> agglutination -> enum unpack)
          5. Key restore
        """
        if not self._v2_initialized:
            self._init_v2()
        if unwrap_ir and isinstance(payload, dict) and {"version", "format", "payload"}.issubset(payload):
            payload = payload["payload"]
        
        if isinstance(payload, dict):
            registry_data = None
            if tables.REGISTRY_KEY in payload:
                registry_data = payload[tables.REGISTRY_KEY]
                payload = {k: v for k, v in payload.items() if k != tables.REGISTRY_KEY}
            
            # Step 1: Restore text values (huffman -> entropy -> numeric -> paninian/structural/enum)
            text_restored = self._apply_decompile_text_to_values(payload)
            
            # Step 2: Restore keys
            key_restored = self.structural.decode_keys(text_restored, registry_data=registry_data)
            
            return key_restored
        elif isinstance(payload, list):
            return [self._decompile_payload_v2(item, unwrap_ir=False) for item in payload]
        elif isinstance(payload, str):
            return self._decompile_text_v2(payload)
        return payload

    def _apply_decompile_text_to_values(self, payload):
        """Recursively decompile text values."""
        if isinstance(payload, dict):
            return {k: self._apply_decompile_text_to_values(v) for k, v in payload.items()}
        elif isinstance(payload, list):
            return [self._apply_decompile_text_to_values(item) for item in payload]
        elif isinstance(payload, str):
            result = self._decompile_text_v2(payload)
            return result
        return payload

    def compile_system_prompt(self, prompt, level=None):
        return self.compile_text(prompt, level=level)

    def decompile_system_prompt(self, prompt, level=None):
        return self.decompile_text(prompt, level=level)

    def get_savings_report(self, original, compressed, level=None):
        target_level = level if level else self.level
        if isinstance(original, str):
            orig_str = original
            comp_str = compressed
        else:
            orig_str = json.dumps(original, separators=(",", ":"))
            comp_str = json.dumps(compressed, separators=(",", ":"))

        orig_len = len(orig_str)
        comp_len = len(comp_str)
        saved = orig_len - comp_len
        pct = round((saved / orig_len) * 100, 2) if orig_len > 0 else 0.0

        orig_tokens = round(orig_len / tables.CHARS_PER_TOKEN_ESTIMATE)
        comp_tokens = round(comp_len / tables.CHARS_PER_TOKEN_ESTIMATE)
        saved_tokens = orig_tokens - comp_tokens

        cost_saved_per_million = round((saved_tokens / 1_000_000) * tables.GPT4O_PRICE_PER_MILLION, 6)

        return {
            "original_chars": orig_len,
            "compressed_chars": comp_len,
            "chars_saved": saved,
            "compression_pct": pct,
            "estimated_tokens_original": orig_tokens,
            "estimated_tokens_compressed": comp_tokens,
            "estimated_tokens_saved": saved_tokens,
            "estimated_cost_saved_usd_gpt4o": cost_saved_per_million,
            "estimated_cost_saved_per_call_usd": cost_saved_per_million,
            "monthly_savings_1k_calls_usd": round(cost_saved_per_million * 1000, 4),
            "monthly_savings_100k_calls_usd": round(cost_saved_per_million * 100_000, 2),
        }

    def _ingest_for_learning(self, payload):
        """Feed payload strings into auto-learner."""
        if not self.auto_dict:
            return
        if isinstance(payload, dict):
            self.auto_dict._ingest_dict(payload)
        elif isinstance(payload, list):
            for item in payload:
                self._ingest_for_learning(item)
        elif isinstance(payload, str) and len(payload) > 10:
            self.auto_dict.learner.ingest_text(payload)
    
    def learn_and_promote(self, top_n=10):
        """Run learning cycle and inject into paninian."""
        if not self.auto_dict:
            return []
        promoted = self.auto_dict.learn(top_n=top_n)
        if promoted:
            self.auto_dict.apply(self)
        return promoted
