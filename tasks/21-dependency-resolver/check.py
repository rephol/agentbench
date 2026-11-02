import itertools, os, random, sys, time
sys.path.insert(0, os.getcwd())
from resolver import resolve, ResolutionError

def fails(req, idx):
    try:
        resolve(req, idx)
    except ResolutionError:
        return True
    return False

# basics
idx = {"a": {"1": {"b": ">=1"}, "2": {"b": ">=2"}}, "b": {"1": {}, "2": {}}}
assert resolve({"a": "*"}, idx) == {"a": "2", "b": "2"}
assert resolve({"a": "<2"}, idx) == {"a": "1", "b": "2"}
assert resolve({}, idx) == {}
# numeric version order and equal-version spelling
idx = {"x": {"1.9": {}, "1.10": {}, "1.10.0": {}}}
r = resolve({"x": "*"}, idx)
assert r["x"] == "1.10", r   # 1.10 and 1.10.0 are equal: the key listed first wins
assert resolve({"x": "<1.10"}, idx) == {"x": "1.9"}
assert resolve({"x": "==1.10.0"}, idx)["x"] == "1.10"
assert resolve({"x": ">=1 !=1.10 <2"}, idx) == {"x": "1.9"}
assert fails({"x": ">1.10"}, idx) and fails({"y": "*"}, idx)
# backtracking: highest a needs a missing/old c
idx = {"a": {"3": {"c": ">=5"}, "2": {"c": ">=1"}}, "c": {"1": {}, "2": {}}}
assert resolve({"a": "*"}, idx) == {"a": "2", "c": "2"}
# conflict between two packages decided by order (a before b)
idx = {"a": {"2": {"c": "==2"}, "1": {"c": "==1"}}, "b": {"2": {"c": "==1"}, "1": {"c": "==2"}}, "c": {"1": {}, "2": {}}}
assert resolve({"a": "*", "b": "*"}, idx) == {"a": "2", "b": "1", "c": "2"}
# deep backtracking
idx = {"a": {"2": {"b": "*"}, "1": {}}, "b": {"2": {"d": "==9"}, "1": {"d": "==1"}}, "d": {"1": {}}, "z": {"1": {"d": "==1"}}}
assert resolve({"a": "*", "z": "*"}, idx) == {"a": "2", "b": "1", "d": "1", "z": "1"}
# dependency of an unchosen version must not leak
idx = {"a": {"2": {"ghost": "*"}, "1": {}}}
assert resolve({"a": "*"}, idx) == {"a": "1"}
# cycles
idx = {"a": {"1": {"b": "*"}}, "b": {"1": {"a": "*"}}}
assert resolve({"a": "*"}, idx) == {"a": "1", "b": "1"}
idx = {"a": {"2": {"b": "*"}, "1": {"b": "*"}}, "b": {"1": {"a": "==1"}}}
assert resolve({"a": "*"}, idx) == {"a": "1", "b": "1"}
# self dependency with an unsatisfied constraint on the chosen version is invalid
idx = {"a": {"2": {"a": "<2"}, "1": {}}}
assert resolve({"a": "*"}, idx) == {"a": "1"}
# a package required with two constraints
idx = {"a": {"1": {"c": "<3"}}, "b": {"1": {"c": ">1"}}, "c": {"1": {}, "2": {}, "3": {}}}
assert resolve({"a": "*", "b": "*"}, idx) == {"a": "1", "b": "1", "c": "2"}
# large no-conflict graph is fast
idx = {}
for i in range(60):
    idx["p%02d" % i] = {str(v): ({"p%02d" % (i + 1): ">=1"} if i < 59 else {}) for v in range(1, 5)}
t = time.time()
r = resolve({"p00": "*"}, idx)
assert len(r) == 60 and all(v == "4" for v in r.values()) and time.time() - t < 2

# oracle: naive depth-first with validation only at the end
def vk(v):
    p = [int(x) for x in v.split(".")]
    while p and p[-1] == 0: p.pop()
    return tuple(p)
import operator
OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt, "==": operator.eq, "!=": operator.ne}
def sat(v, c):
    if c == "*": return True
    for t in c.split():
        for op in (">=", "<=", "==", "!=", ">", "<"):
            if t.startswith(op):
                if not OPS[op](vk(v), vk(t[len(op):])): return False
                break
    return True
def oracle(req, idx):
    def valid(ch):
        need = dict()
        for p, c in req.items(): need.setdefault(p, []).append(c)
        for p, v in ch.items():
            for d, c in idx[p][v].items(): need.setdefault(d, []).append(c)
        return set(ch) == set(need) and all(all(sat(ch[p], c) for c in cs) for p, cs in need.items())
    def go(ch):
        need = set(req)
        for p, v in ch.items(): need |= set(idx[p][v])
        todo = sorted(need - set(ch))
        if not todo:
            return dict(ch) if valid(ch) else None
        p = todo[0]
        for v in sorted(idx.get(p, {}), key=vk, reverse=True):
            ch[p] = v
            r = go(ch)
            del ch[p]
            if r: return r
        return None
    return go({})
random.seed(5)
names = list("abcdef")
cons = ["*", ">=1", ">=2", "<2", "<3", "==1", "==2", "==3", "!=2", ">1 <3", "<=1"]
for _ in range(400):
    idx = {}
    for n in names[: random.randint(2, 6)]:
        idx[n] = {}
        for v in random.sample(["1", "2", "3", "2.0"], random.randint(1, 3)):
            idx[n][v] = {d: random.choice(cons) for d in random.sample(names, random.randint(0, 2))}
    req = {d: random.choice(cons) for d in random.sample(names, random.randint(1, 2))}
    want = oracle(req, idx)
    try:
        got = resolve(req, idx)
    except ResolutionError:
        got = None
    assert got == want, (req, idx, want, got)
print("ok")
