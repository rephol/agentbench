import time
from collections import OrderedDict


class TTLCache:
    """LRU cache with per-entry expiry; see task statement."""

    def __init__(self, capacity, ttl, clock=time.monotonic):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            raise ValueError("capacity must be an int >= 1")
        self._check_ttl(ttl)
        self.capacity = capacity
        self.ttl = ttl
        self.clock = clock
        self._d = OrderedDict()  # key -> (value, expires_at), LRU first
        self._hits = self._misses = self._evictions = self._expirations = 0

    @staticmethod
    def _check_ttl(ttl):
        if isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or ttl <= 0:
            raise ValueError("ttl must be a number > 0")

    def _expired(self, entry, now):
        return now >= entry[1]

    def set(self, key, value, ttl=None):
        if ttl is None:
            ttl = self.ttl
        else:
            self._check_ttl(ttl)
        now = self.clock()
        if key in self._d:
            if self._expired(self._d[key], now):
                self._expirations += 1
            del self._d[key]
        else:
            for k in [k for k, e in self._d.items() if self._expired(e, now)]:
                del self._d[k]
                self._expirations += 1
            if len(self._d) >= self.capacity:
                self._d.popitem(last=False)
                self._evictions += 1
        self._d[key] = (value, now + ttl)

    def get(self, key, default=None):
        entry = self._d.get(key)
        if entry is None:
            self._misses += 1
            return default
        if self._expired(entry, self.clock()):
            del self._d[key]
            self._expirations += 1
            self._misses += 1
            return default
        self._d.move_to_end(key)
        self._hits += 1
        return entry[0]

    def peek(self, key, default=None):
        entry = self._d.get(key)
        if entry is None or self._expired(entry, self.clock()):
            return default
        return entry[0]

    def delete(self, key):
        entry = self._d.pop(key, None)
        if entry is None:
            return False
        if self._expired(entry, self.clock()):
            self._expirations += 1
            return False
        return True

    def purge(self):
        now = self.clock()
        dead = [k for k, e in self._d.items() if self._expired(e, now)]
        for k in dead:
            del self._d[k]
        self._expirations += len(dead)
        return len(dead)

    def __len__(self):
        now = self.clock()
        return sum(1 for e in self._d.values() if not self._expired(e, now))

    def __contains__(self, key):
        entry = self._d.get(key)
        return entry is not None and not self._expired(entry, self.clock())

    def keys(self):
        now = self.clock()
        return [k for k, e in self._d.items() if not self._expired(e, now)]

    def stats(self):
        return {"hits": self._hits, "misses": self._misses,
                "evictions": self._evictions, "expirations": self._expirations}
