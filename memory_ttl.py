# memory_ttl.py
# Time-bound, opt-in memory store
# Explicit reason required. TTL enforced.

import time
from typing import Dict, List


class MemoryStore:
    def __init__(self):
        self._store: List[Dict] = []

    def write(self, content: str, reason: str, ttl_seconds: int) -> None:
        """
        Store memory with explicit reason and expiration.
        """
        expires_at = time.time() + ttl_seconds
        self._store.append({
            "content": content,
            "reason": reason,
            "expires_at": expires_at
        })

    def read(self) -> List[Dict]:
        """
        Read non-expired memory entries.
        """
        now = time.time()
        self._store = [m for m in self._store if m["expires_at"] > now]
        return list(self._store)

    def clear(self) -> None:
        """
        Delete all memory immediately.
        """
        self._store.clear()

