"""Cache read_only tool outputs and detect duplicate results across calls."""

from __future__ import annotations

import hashlib
import json
import time


class OutputCache:
    """Lightweight in-memory cache for read_only tool outputs + duplicate detection.

    Two orthogonal features:
      - **Cache**: same tool + same params → skip re-execution (read_only tools only).
      - **Dedup**: regardless of cache hit/miss, if returned content is identical to
        a recent output, shorten it to a note.
    """

    def __init__(self, ttl: int = 60, max_entries: int = 100, max_history: int = 20):
        self._ttl = ttl
        self._max_entries = max_entries
        self._cache: dict[str, tuple[float, str]] = {}
        self._fingerprints: list[str] = []
        self._call_count = 0

    # -- caching ----------------------------------------------------------------

    def get(self, tool_name: str, params: dict) -> tuple[str, int] | None:
        """Return (cached_result, age_seconds) or None on miss/expiry."""
        key = self._key(tool_name, params)
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, result = entry
        age = int(time.time() - ts)
        if age > self._ttl:
            del self._cache[key]
            return None
        return result, age

    def put(self, tool_name: str, params: dict, result: str) -> None:
        """Store a result in the cache."""
        key = self._key(tool_name, params)
        self._cache[key] = (time.time(), result)
        if len(self._cache) > self._max_entries:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]

    # -- duplicate detection ---------------------------------------------------

    def check_duplicate(self, result: str) -> bool:
        """Return True if *result* was already returned recently."""
        self._call_count += 1
        fp = hashlib.sha256(result.encode("utf-8", errors="replace")).hexdigest()
        if fp in self._fingerprints:
            return True
        self._fingerprints.append(fp)
        if len(self._fingerprints) > 20:
            self._fingerprints.pop(0)
        return False

    # -- internal ----------------------------------------------------------------

    @staticmethod
    def _key(tool_name: str, params: dict) -> str:
        serialized = json.dumps(params, sort_keys=True, ensure_ascii=False)
        h = hashlib.md5(serialized.encode()).hexdigest()[:16]
        return f"{tool_name}:{h}"

    def clear(self) -> None:
        """Clear all cached entries and history."""
        self._cache.clear()
        self._fingerprints.clear()
        self._call_count = 0
