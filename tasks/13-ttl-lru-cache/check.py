import os, sys
sys.path.insert(0, os.getcwd())
import random
from cache import TTLCache

class Clock:
    def __init__(self): self.t = 1000.0
    def __call__(self): return self.t
c = Clock()
for bad in ((0, 1), (-1, 1), (2.5, 1), (True, 1), (2, 0), (2, -1), (2, "x")):
    try:
        TTLCache(*bad, clock=c); raise SystemExit("expected ValueError %r" % (bad,))
    except ValueError:
        pass
k = TTLCache(2, 10, clock=c)
k.set("a", 1); k.set("b", 2)
assert k.get("a") == 1                      # a is now MRU
k.set("c", 3)                               # evicts b
assert k.get("b", "none") == "none" and k.keys() == ["a", "c"]
assert k.stats() == {"hits": 1, "misses": 1, "evictions": 1, "expirations": 0}, k.stats()
c.t += 9.999
assert "a" in k
c.t += 0.001                                # exactly ttl: expired
assert "a" not in k and len(k) == 0 and k.keys() == []
assert k.stats()["expirations"] == 0, "len/in must not count expirations"
assert k.get("a", "gone") == "gone"
assert k.stats() == {"hits": 1, "misses": 2, "evictions": 1, "expirations": 1}, k.stats()
# get does not extend ttl; set does
k = TTLCache(3, 10, clock=c)
k.set("a", 1); c.t += 6; assert k.get("a") == 1; c.t += 5
assert k.get("a") is None
k.set("a", 1); c.t += 6; k.set("a", 2); c.t += 6
assert k.get("a") == 2
# per-entry ttl
k = TTLCache(3, 100, clock=c)
k.set("short", 1, ttl=1); k.set("long", 2)
c.t += 2
assert k.peek("short") is None and k.peek("long") == 2
assert k.purge() == 1 and k.stats()["expirations"] == 1 and k.purge() == 0
try:
    k.set("x", 1, ttl=0); raise SystemExit("expected ValueError")
except ValueError:
    pass
# new key purges expired before evicting a live entry
k = TTLCache(2, 10, clock=c)
k.set("a", 1, ttl=1); k.set("b", 2)
c.t += 2
k.set("c", 3)
assert k.keys() == ["b", "c"] and k.stats() == {"hits": 0, "misses": 0, "evictions": 0, "expirations": 1}, k.stats()
# re-set of an expired key counts an expiration, no eviction
k = TTLCache(1, 10, clock=c)
k.set("a", 1); c.t += 11; k.set("a", 2)
assert k.stats() == {"hits": 0, "misses": 0, "evictions": 0, "expirations": 1} and k.get("a") == 2
# peek does not touch recency
k = TTLCache(2, 100, clock=c)
k.set("a", 1); k.set("b", 2); assert k.peek("a") == 1; k.set("c", 3)
assert k.keys() == ["b", "c"] and k.stats()["hits"] == 0
# delete
k = TTLCache(3, 5, clock=c)
k.set("a", 1); k.set("b", 2)
assert k.delete("a") is True and k.delete("a") is False
c.t += 5
assert k.delete("b") is False and k.stats()["expirations"] == 1 and len(k) == 0
# model-based randomized comparison
class Model:
    def __init__(s, cap, ttl): s.cap, s.ttl, s.e, s.st = cap, ttl, [], dict(hits=0, misses=0, evictions=0, expirations=0)
    def idx(s, key):
        for i, x in enumerate(s.e):
            if x[0] == key: return i
        return -1
    def dead(s, x, now): return now >= x[2]
    def set(s, key, v, now, ttl=None):
        ttl = s.ttl if ttl is None else ttl
        i = s.idx(key)
        if i >= 0:
            if s.dead(s.e[i], now): s.st["expirations"] += 1
            s.e.pop(i)
        else:
            keep = []
            for x in s.e:
                if s.dead(x, now): s.st["expirations"] += 1
                else: keep.append(x)
            s.e = keep
            if len(s.e) >= s.cap:
                s.e.pop(0); s.st["evictions"] += 1
        s.e.append([key, v, now + ttl])
    def get(s, key, now):
        i = s.idx(key)
        if i < 0: s.st["misses"] += 1; return None
        x = s.e[i]
        if s.dead(x, now):
            s.e.pop(i); s.st["expirations"] += 1; s.st["misses"] += 1; return None
        s.e.append(s.e.pop(i)); s.st["hits"] += 1; return x[1]
    def delete(s, key, now):
        i = s.idx(key)
        if i < 0: return False
        x = s.e.pop(i)
        if s.dead(x, now): s.st["expirations"] += 1; return False
        return True
    def purge(s, now):
        n = len(s.e); s.e = [x for x in s.e if not s.dead(x, now)]
        s.st["expirations"] += n - len(s.e); return n - len(s.e)
    def keys(s, now): return [x[0] for x in s.e if not s.dead(x, now)]
for seed in range(40):
    rnd = random.Random(seed)
    c = Clock(); cap = rnd.randint(1, 5)
    k = TTLCache(cap, 6, clock=c); m = Model(cap, 6)
    for step in range(300):
        c.t += rnd.choice([0, 0, 1, 1, 2, 5])
        key = rnd.choice("abcdefg"); op = rnd.choice(["set", "set", "get", "get", "del", "purge", "peek"])
        if op == "set":
            ttl = rnd.choice([None, None, 1, 3, 20]); v = rnd.random()
            k.set(key, v, ttl=ttl); m.set(key, v, c.t, ttl)
        elif op == "get":
            assert k.get(key) == m.get(key, c.t), (seed, step)
        elif op == "del":
            assert k.delete(key) == m.delete(key, c.t), (seed, step)
        elif op == "purge":
            assert k.purge() == m.purge(c.t), (seed, step)
        else:
            i = m.idx(key); exp = m.e[i][1] if i >= 0 and not m.dead(m.e[i], c.t) else None
            assert k.peek(key) == exp
        assert k.keys() == m.keys(c.t) and len(k) == len(m.keys(c.t)), (seed, step)
        assert k.stats() == m.st, (seed, step, k.stats(), m.st)
print("ok")
