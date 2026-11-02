import time


class TTLCache:
    """An LRU cache whose entries also expire.

    TTLCache(capacity, ttl, clock=time.monotonic)
      capacity: max number of entries, an int >= 1 (else ValueError).
      ttl: default lifetime in seconds, a number > 0 (else ValueError).
      clock: zero-argument callable returning the current time in seconds.

    An entry written by set() at time t with lifetime L is expired once clock() >= t + L.

    set(key, value, ttl=None)
      Stores the entry; `ttl`, if given, overrides the default lifetime for this entry
      (must be a number > 0, else ValueError). The entry becomes the most recently used.
      - If the key is already stored, its value, expiry and recency are replaced and no
        eviction happens. If the old entry had already expired, count one expiration.
      - If the key is new: first remove every expired entry (one expiration each); then,
        if the cache still holds `capacity` entries, evict the least recently used entry
        and count one eviction. Then insert.
    get(key, default=None)
      A live entry counts as a hit, becomes the most recently used, and its expiry is NOT
      extended. A missing key counts as a miss. A stored but expired entry is removed,
      counts one expiration AND one miss. Returns the value, or `default` on a miss.
    peek(key, default=None)
      Like get for live entries but changes nothing (no recency change, no counters).
      Expired or missing keys return `default` and are not removed.
    delete(key) -> bool
      True if a live entry was removed. An expired entry is removed too (counting one
      expiration) but returns False. A missing key returns False.
    purge() -> int
      Removes all expired entries, counts one expiration each, returns how many.
    len(cache)
      Number of live (unexpired) entries. `key in cache` is True only for live entries.
      Neither removes anything or changes counters.
    keys()
      Live keys, least recently used first. Changes nothing.
    stats()
      {"hits": int, "misses": int, "evictions": int, "expirations": int}
    """

    def __init__(self, capacity, ttl, clock=time.monotonic):
        raise NotImplementedError
