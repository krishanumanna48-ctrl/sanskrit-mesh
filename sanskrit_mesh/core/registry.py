import json
import threading
from collections import deque

from sanskrit_mesh.core import tables


class DynamicRegistry:
    """Thread-safe dynamic registry for runtime key -> marker mappings.

    Enhancements:
    - Uses a deque for marker pool (fast popleft).
    - Adds a lock for thread-safety.
    - Safe `load` merging with collision handling.
    - File persistence helpers: `persist` and `restore`.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._forward = {}
        self._reverse = {}
        self._marker_pool = deque(self._seed_pool())

    def _seed_pool(self):
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        used = set()
        for v in tables.V1_KEY_MAP.values():
            used.add(v)
        for v in tables.EXTENDED_KEY_MAP.values():
            used.add(v)
        pool = []
        # single-char candidates first
        for a in chars:
            if a in used:
                continue
            pool.append(a)
        # then two-char combos
        for a in chars:
            for b in chars:
                combo = a + b
                if combo in used:
                    continue
                pool.append(combo)
                if len(pool) >= 2000:
                    return pool
        return pool

    def get_or_assign(self, key):
        with self._lock:
            if key in self._forward:
                return self._forward[key]
            if not self._marker_pool:
                return None
            marker = self._marker_pool.popleft()
            # defensively avoid accidental collisions
            if marker in self._reverse:
                # should be rare, try to find next available
                while self._marker_pool and marker in self._reverse:
                    marker = self._marker_pool.popleft()
                if marker in self._reverse:
                    return None
            self._forward[key] = marker
            self._reverse[marker] = key
            return marker

    def lookup(self, marker):
        with self._lock:
            return self._reverse.get(marker)

    def dump(self):
        with self._lock:
            return dict(self._forward)

    def load(self, data):
        """Merge mappings from `data` (dict or JSON string).

        If a provided marker collides with an existing mapping, a new marker
        will be assigned for that key and the collision will be noted.
        """
        if not data:
            return
        loaded = data
        if isinstance(data, str):
            loaded = json.loads(data)
        with self._lock:
            for k, v in loaded.items():
                # if mapping already exists and matches, skip
                if k in self._forward and self._forward[k] == v:
                    continue
                # if marker is used by another key, resolve by allocating a new marker
                if v in self._reverse and self._reverse[v] != k:
                    # collision — pick next available marker
                    new_marker = None
                    while self._marker_pool:
                        candidate = self._marker_pool.popleft()
                        if candidate not in self._reverse and candidate not in loaded.values():
                            new_marker = candidate
                            break
                    if new_marker is None:
                        # no markers left; skip assignment for this key
                        continue
                    self._forward[k] = new_marker
                    self._reverse[new_marker] = k
                else:
                    self._forward[k] = v
                    self._reverse[v] = k
                    # remove from pool if present
                    try:
                        if v in self._marker_pool:
                            # deque doesn't have remove in older Python; use list remove safely
                            self._marker_pool.remove(v)
                    except Exception:
                        try:
                            self._marker_pool = deque(x for x in self._marker_pool if x != v)
                        except Exception:
                            pass

    def persist(self, path):
        """Write registry forward map to `path` as JSON."""
        data = self.dump()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    def restore(self, path):
        """Load registry mappings from a JSON file at `path`."""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        self.load(data)

    def reset(self):
        with self._lock:
            self._forward = {}
            self._reverse = {}
            self._marker_pool = deque(self._seed_pool())
