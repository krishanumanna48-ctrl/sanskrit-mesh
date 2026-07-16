import json
import re
from collections import Counter

from sanskrit_mesh.core import tables


class StructuralLayer:
    def __init__(self, registry=None):
        self.registry = registry
        merged = {}
        merged.update(tables.V1_KEY_MAP)
        merged.update(tables.EXTENDED_KEY_MAP)
        self.full_key_map = merged
        # Build reverse map preferring V1 mappings when collisions occur.
        reverse = {}
        for k, v in tables.V1_KEY_MAP.items():
            reverse[v] = k
        for k, v in tables.EXTENDED_KEY_MAP.items():
            if v not in reverse:
                reverse[v] = k
        self.reverse_key_map = reverse
        self.agglutination = tables.ENGLISH_AGGLOUTINATION_PHRASES
        self.aglutination_inverse = {v: k for k, v in self.agglutination.items()}
        self._agglut_sorted = sorted(self.agglutination.keys(), key=len, reverse=True)
        self._agglut_inverse_sorted = sorted(self.aglutination_inverse.keys(), key=len, reverse=True)
        
        # C: Enum packing maps
        self._bool_map = {"true": "τ", "false": "φ", "True": "τ", "False": "φ"}
        self._bool_inverse = {v: k for k, v in self._bool_map.items()}
        self._status_map = {"completed": "C", "in_progress": "IP", "failed": "F", "pending": "P", "running": "R", "cancelled": "CX"}
        self._status_inverse = {v: k for k, v in self._status_map.items()}
        
        # D: Tool call tracking
        self._tool_name_counter = 0
        self._tool_name_map = {}
        self._tool_name_inverse = {}
        
        # E: Schema inference cache
        self._schema_cache = {}
        self._schema_counter = 0
        
        # F: Null omission headers
        self._null_header_key = "⟦nulls⟧"
        
        # G: String interning
        self._string_table = {}
        self._string_counter = 0

    def encode_text(self, text):
        if not isinstance(text, str) or not text:
            return text
        result = text
        for phrase in self._agglut_sorted:
            if phrase in result:
                result = result.replace(phrase, self.agglutination[phrase])
        return result

    def _pack_enums_in_text(self, text):
        """C: Pack booleans and common status strings using word-boundary regex."""
        if not isinstance(text, str):
            return text
        result = text
        # Use word boundaries to avoid partial matches inside words
        for eng, glyph in self._bool_map.items():
            result = re.sub(r'(?<!\w)' + re.escape(eng) + r'(?!\w)', glyph, result)
        for eng, glyph in self._status_map.items():
            result = re.sub(r'(?<!\w)' + re.escape(eng) + r'(?!\w)', glyph, result)
        return result

    def _unpack_enums_in_text(self, text):
        """C: Unpack booleans and status strings using word-boundary regex."""
        if not isinstance(text, str):
            return text
        result = text
        for glyph, eng in self._status_inverse.items():
            result = re.sub(r'(?<!\w)' + re.escape(glyph) + r'(?!\w)', eng, result)
        for glyph, eng in self._bool_inverse.items():
            result = re.sub(r'(?<!\w)' + re.escape(glyph) + r'(?!\w)', eng, result)
        return result

    def _compress_tool_calls(self, payload):
        """D: Compress repeated tool names in lists of tool calls."""
        if not isinstance(payload, list):
            return payload
        if len(payload) < 2:
            return payload
        if not all(isinstance(item, dict) for item in payload):
            return payload
        
        # Check if all items have "name" key
        if not all("name" in item for item in payload):
            return payload
        
        # Count tool names
        name_counts = Counter(item.get("name") for item in payload if isinstance(item, dict))
        if not name_counts:
            return payload
        
        # Find repeated names (appears 2+ times)
        repeated = {name: count for name, count in name_counts.items() if count >= 2}
        if not repeated:
            return payload
        
        # Assign shorthand glyphs
        for name in repeated:
            if name not in self._tool_name_map:
                glyph = f"⟦t{self._tool_name_counter}⟧"
                self._tool_name_map[name] = glyph
                self._tool_name_inverse[glyph] = name
                self._tool_name_counter += 1
        
        # Build compressed list
        compressed = []
        for item in payload:
            if not isinstance(item, dict):
                compressed.append(item)
                continue
            name = item.get("name")
            if name in self._tool_name_map:
                new_item = {k: v for k, v in item.items() if k != "name"}
                compressed.append(new_item)
            else:
                compressed.append(item)
        
        # Add header
        header = {"⟦tools⟧": {glyph: name for name, glyph in self._tool_name_map.items() if name in repeated}}
        return [header] + compressed

    def _decompress_tool_calls(self, payload):
        """D: Restore repeated tool names."""
        if not isinstance(payload, list) or len(payload) < 1:
            return payload
        
        # Check for header
        if not isinstance(payload[0], dict):
            return payload
        if "⟦tools⟧" not in payload[0]:
            return payload
        
        tool_header = payload[0]["⟦tools⟧"]
        tool_name_map = {glyph: name for glyph, name in tool_header.items()}
        
        # Restore tool names
        restored = []
        for item in payload[1:]:
            if not isinstance(item, dict):
                restored.append(item)
                continue
            # Check if any key is a tool glyph
            new_item = {}
            for k, v in item.items():
                if k in tool_name_map:
                    new_item["name"] = tool_name_map[k]
                else:
                    new_item[k] = v
            # If no tool name found, keep as-is (shouldn't happen)
            if "name" not in new_item:
                new_item = item
            restored.append(new_item)
        
        return restored

    def _infer_list_schema(self, payload):
        """E: Compress arrays of uniform dicts by extracting common keys."""
        if not isinstance(payload, list) or len(payload) < 2:
            return payload
        if not all(isinstance(item, dict) for item in payload):
            return payload
        
        # Check if all dicts have same keys
        key_sets = [set(item.keys()) for item in payload]
        if not all(ks == key_sets[0] for ks in key_sets):
            return payload
        
        common_keys = sorted(key_sets[0])
        if not common_keys:
            return payload
        
        # Build schema header
        schema_id = f"schm{self._schema_counter}"
        self._schema_counter += 1
        self._schema_cache[schema_id] = common_keys
        
        # Build row-based payload
        rows = []
        for item in payload:
            row = [str(item[k]) for k in common_keys]
            rows.append(",".join(row))
        
        return [schema_id, rows]

    def _restore_list_schema(self, payload):
        """E: Restore arrays compressed with schema inference."""
        if not isinstance(payload, list) or len(payload) < 2:
            return payload
        if not isinstance(payload[0], str) or not payload[0].startswith("schm"):
            return payload
        
        schema_id = payload[0]
        if schema_id not in self._schema_cache:
            return payload
        
        common_keys = self._schema_cache[schema_id]
        rows = payload[1]
        
        restored = []
        for row in rows:
            values = row.split(",")
            obj = {k: values[i] if i < len(values) else "" for i, k in enumerate(common_keys)}
            restored.append(obj)
        
        return restored

    def _omit_nulls(self, payload):
        """F: Omit null/empty values, track in header."""
        if not isinstance(payload, dict):
            return payload
        
        null_positions = []
        clean = {}
        for k, v in payload.items():
            if v is None or v == "" or v == [] or v == {}:
                null_positions.append(k)
            else:
                clean[k] = v
        
        if not null_positions:
            return clean
        
        clean[self._null_header_key] = null_positions
        return clean

    def _restore_nulls(self, payload):
        """F: Restore omitted nulls from header."""
        if not isinstance(payload, dict):
            return payload
        
        null_positions = payload.pop(self._null_header_key, [])
        if not null_positions:
            return payload
        
        for key in null_positions:
            if key not in payload:
                payload[key] = None
        
        return payload

    def _intern_strings(self, payload):
        """G: Intern repeated strings across payload."""
        if not isinstance(payload, dict):
            return payload
        
        string_counts = Counter()
        def _count_strings(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    _count_strings(v)
            elif isinstance(obj, list):
                for item in obj:
                    _count_strings(item)
            elif isinstance(obj, str) and len(obj) > 5:
                string_counts[obj] += 1
        
        _count_strings(payload)
        
        # Find strings appearing 2+ times
        repeated = {s for s, count in string_counts.items() if count >= 2}
        if not repeated:
            return payload
        
        # Assign intern glyphs
        intern_map = {}
        for s in repeated:
            if s not in self._string_table:
                glyph = f"⟦s{self._string_counter}⟧"
                self._string_table[s] = glyph
                self._string_counter += 1
            intern_map[s] = self._string_table[s]
        
        # Build intern table header
        header = {"⟦intern⟧": {v: k for k, v in intern_map.items()}}
        
        # Replace strings with glyphs
        def _intern(obj):
            if isinstance(obj, dict):
                return {k: _intern(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_intern(item) for item in obj]
            elif isinstance(obj, str) and obj in intern_map:
                return intern_map[obj]
            return obj
        
        interned = _intern(payload)
        return [header, interned]

    def _deintern_strings(self, payload):
        """G: Restore interned strings."""
        if not isinstance(payload, list) or len(payload) < 2:
            return payload
        if not isinstance(payload[0], dict) or "⟦intern⟧" not in payload[0]:
            return payload
        
        intern_table = {v: k for k, v in payload[0]["⟦intern⟧"].items()}
        
        def _deintern(obj):
            if isinstance(obj, dict):
                return {k: _deintern(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_deintern(item) for item in obj]
            elif isinstance(obj, str) and obj in intern_table:
                return intern_table[obj]
            return obj
        
        return _deintern(payload[1])

    def _normalize_floats(self, payload):
        """H: Normalize float precision in payload."""
        if isinstance(payload, float):
            # Round to 6 significant figures
            if payload == 0.0:
                return 0.0
            return round(payload, 6)
        elif isinstance(payload, dict):
            return {k: self._normalize_floats(v) for k, v in payload.items()}
        elif isinstance(payload, list):
            return [self._normalize_floats(item) for item in payload]
        return payload

    def decode_text(self, text):
        if not isinstance(text, str) or not text:
            return text
        result = text
        for token in self._agglut_inverse_sorted:
            if token in result:
                result = result.replace(token, self.aglutination_inverse[token])
        return result.replace("accessControlManagement", "access control management")

    def encode_keys(self, payload):
        return self._walk_encode(payload)

    def encode_keys_only(self, payload):
        """Encode keys only, without applying text layers to values."""
        return self._walk_encode_keys_only(payload)

    def decode_keys(self, payload, registry_data=None):
        """Decode keys only, without touching string values."""
        if registry_data and self.registry is not None:
            self.registry.load(registry_data)
        return self._walk_decode_keys_only(payload)

    def _encode_key(self, key):
        if not isinstance(key, str):
            return key
        if key in self.full_key_map:
            return self.full_key_map[key]
        if self.registry is not None:
            mapped = self.registry.get_or_assign(key)
            if mapped is not None:
                return mapped
        return key

    def _decode_key(self, key):
        if not isinstance(key, str):
            return key
        if key in self.reverse_key_map:
            return self.reverse_key_map[key]
        if self.registry is not None:
            original = self.registry.lookup(key)
            if original is not None:
                return original
        return key

    def _walk_encode_keys_only(self, payload):
        """Walk payload and encode keys only — no text value changes."""
        if isinstance(payload, dict):
            new_obj = {}
            for k, v in payload.items():
                new_key = self._encode_key(k)
                if isinstance(v, (dict, list)):
                    new_obj[new_key] = self._walk_encode_keys_only(v)
                else:
                    new_obj[new_key] = v
            return new_obj
        elif isinstance(payload, list):
            return [self._walk_encode_keys_only(item) for item in payload]
        return payload

    def _walk_decode_keys_only(self, payload):
        """Walk payload and decode keys only — no text value changes."""
        if isinstance(payload, dict):
            new_obj = {}
            for k, v in payload.items():
                new_key = self._decode_key(k)
                if isinstance(v, (dict, list)):
                    new_obj[new_key] = self._walk_decode_keys_only(v)
                else:
                    new_obj[new_key] = v
            return new_obj
        elif isinstance(payload, list):
            return [self._walk_decode_keys_only(item) for item in payload]
        return payload

    def encode_payload(self, payload, safe_mode=True):
        """Full structural encoding of payload: keys + text values.
        
        safe_mode=True: only keys + enums (lossless proven).
        safe_mode=False: add dedup, tool calls, schema, nulls, interning (experimental).
        """
        if not isinstance(payload, dict):
            return payload
        
        # Step 1: Keys
        key_encoded = self._walk_encode_keys_only(payload)
        
        # Step 2: Text values (agglutination + enums)
        text_encoded = self._encode_values_with_text_layers(key_encoded)
        
        if not safe_mode:
            # Experimental B-H optimizations (may cause lossiness)
            tool_compressed = self._compress_tool_calls(text_encoded)
            schema_compressed = self._infer_list_schema(tool_compressed)
            null_omitted = self._omit_nulls(schema_compressed)
            interned = self._intern_strings(null_omitted)
            float_normalized = self._normalize_floats(interned)
            return float_normalized
        
        return text_encoded

    def _encode_values_with_text_layers(self, payload):
        """Apply text encoders (entropy/agglutination/enums) to all string values."""
        if isinstance(payload, dict):
            new_obj = {}
            for k, v in payload.items():
                if isinstance(v, (dict, list)):
                    new_obj[k] = self._encode_values_with_text_layers(v)
                elif isinstance(v, str):
                    new_obj[k] = self.encode_text_with_enums(v)
                else:
                    new_obj[k] = v
            return new_obj
        elif isinstance(payload, list):
            return [self._encode_values_with_text_layers(item) for item in payload]
        elif isinstance(payload, str):
            return self.encode_text_with_enums(payload)
        return payload

    def encode_text_with_enums(self, text):
        """Encode text with agglutination + enum packing."""
        if not isinstance(text, str) or not text:
            return text
        # Skip enum packing if text contains paninian tokens (|...|) to avoid corruption
        if '|' in text:
            return text
        result = self.encode_text(text)
        result = self._pack_enums_in_text(result)
        return result

    def decode_text_with_enums(self, text):
        """Decode text with enum unpacking."""
        if not isinstance(text, str) or not text:
            return text
        # Skip enum unpacking if text contains paninian tokens (|...|)
        if '|' in text:
            return text
        result = self._unpack_enums_in_text(text)
        result = self.decode_text(result)
        return result

    def decode_payload(self, payload, registry_data=None):
        """Full structural decoding: reverse of encode_payload."""
        if not isinstance(payload, dict) and not isinstance(payload, list):
            return payload
        
        if registry_data and self.registry is not None:
            self.registry.load(registry_data)
        
        # Text value decoding first
        text_decoded = self._decode_values_with_text_layers(payload)
        
        # Key decoding
        return self._walk_decode(text_decoded)

    def _decode_values_with_text_layers(self, payload):
        """Apply text decoders to all string values."""
        if isinstance(payload, dict):
            new_obj = {}
            for k, v in payload.items():
                if k == "⟦tools⟧":
                    new_obj[k] = v
                    continue
                if isinstance(v, (dict, list)):
                    new_obj[k] = self._decode_values_with_text_layers(v)
                elif isinstance(v, str):
                    new_obj[k] = self.decode_text_with_enums(v)
                else:
                    new_obj[k] = v
            return new_obj
        elif isinstance(payload, list):
            return [self._decode_values_with_text_layers(item) for item in payload]
        elif isinstance(payload, str):
            return self.decode_text_with_enums(payload)
        return payload

    def _walk_encode(self, payload):
        if isinstance(payload, dict):
            new_obj = {}
            for k, v in payload.items():
                new_key = self._encode_key(k)
                if isinstance(v, (dict, list)):
                    new_obj[new_key] = self._walk_encode(v)
                elif isinstance(v, str):
                    new_obj[new_key] = self.encode_text_with_enums(v)
                else:
                    new_obj[new_key] = v
            return new_obj
        elif isinstance(payload, list):
            return [self._walk_encode(item) for item in payload]
        elif isinstance(payload, str):
            return self.encode_text_with_enums(payload)
        return payload

    def _walk_decode(self, payload):
        if isinstance(payload, dict):
            new_obj = {}
            for k, v in payload.items():
                new_key = self._decode_key(k)
                if k == "⟦tools⟧":
                    new_obj[new_key] = v
                    continue
                if isinstance(v, (dict, list)):
                    new_obj[new_key] = self._walk_decode(v)
                elif isinstance(v, str):
                    new_obj[new_key] = self.decode_text_with_enums(v)
                else:
                    new_obj[new_key] = v
            return new_obj
        elif isinstance(payload, list):
            return [self._walk_decode(item) for item in payload]
        elif isinstance(payload, str):
            return self.decode_text_with_enums(payload)
        return payload
