import os, random, sys
sys.path.insert(0, os.getcwd())
from leaderboard import Board

def raises(exc, f, *a):
    try:
        f(*a)
    except exc:
        return True
    return False

b = Board()
for n, s in [("dan", 70), ("amy", 90), ("cat", 80), ("bob", 80), ("eve", 90.0)]:
    b.set_score(n, s)
assert len(b) == 5
assert b.top(10) == [(1, "amy", 90), (1, "eve", 90.0), (3, "bob", 80), (3, "cat", 80), (5, "dan", 70)]
assert [b.rank(n) for n in ["amy", "eve", "bob", "cat", "dan"]] == [1, 1, 3, 3, 5]
assert b.top(2) == [(1, "amy", 90), (1, "eve", 90.0)] and b.top(0) == [] and b.top(-3) == []
assert b.page(1, 2) == b.top(2) and b.page(2, 2) == [(3, "bob", 80), (3, "cat", 80)] and b.page(3, 2) == [(5, "dan", 70)] and b.page(4, 2) == []
assert b.page(1, 100) == b.top(5)
assert raises(ValueError, b.page, 0, 2) and raises(ValueError, b.page, 1, 0) and raises(ValueError, b.page, -1, 2)
assert b.around("bob", 1) == [(1, "eve", 90.0), (3, "bob", 80), (3, "cat", 80)]
assert b.around("amy", 1) == [(1, "amy", 90), (1, "eve", 90.0)]
assert b.around("dan", 2) == [(3, "bob", 80), (3, "cat", 80), (5, "dan", 70)]
assert b.around("cat", 0) == [(3, "cat", 80)] and len(b.around("cat", 99)) == 5
assert raises(ValueError, b.around, "cat", -1) and raises(KeyError, b.around, "zed", 1)
assert raises(KeyError, b.rank, "zed") and raises(KeyError, b.remove, "zed") and raises(KeyError, b.percentile, "zed")
assert b.percentile("dan") == 0.0 and b.percentile("amy") == 100.0 * 3 / 4 and b.percentile("bob") == 100.0 * 1 / 4
assert isinstance(b.percentile("dan"), float)
# case-sensitive name order: uppercase sorts before lowercase
c = Board(); c.set_score("b", 1); c.set_score("B", 1); c.set_score("a", 1)
assert c.top(3) == [(1, "B", 1), (1, "a", 1), (1, "b", 1)]
# single player
s = Board(); s.set_score("solo", 5)
assert s.percentile("solo") == 100.0 and s.rank("solo") == 1 and s.around("solo", 3) == [(1, "solo", 5)]
# replacing a score moves the player; removal re-ranks
b.set_score("dan", 95)
assert b.top(1) == [(1, "dan", 95)] and b.rank("amy") == 2 and len(b) == 5
b.set_score("dan", 95)
assert len(b) == 5
b.remove("dan")
assert b.rank("amy") == 1 and len(b) == 4 and raises(KeyError, b.rank, "dan")
# floats and ints compare equal
f = Board(); f.set_score("x", 1); f.set_score("y", 1.0); f.set_score("z", 0.5)
assert [r for r, _, _ in f.top(3)] == [1, 1, 3] and f.percentile("x") == 50.0
# validation
assert raises(ValueError, b.set_score, "n", float("nan")) and raises(TypeError, b.set_score, "n", True)
assert "n" not in [n for _, n, _ in b.top(99)]
# empty board
e = Board()
assert e.top(3) == [] and e.page(1, 3) == [] and len(e) == 0
# randomized oracle
random.seed(2)
names = ["n%02d" % i for i in range(30)]
for _ in range(200):
    bd = Board(); ref = {}
    for _ in range(random.randint(1, 30)):
        n = random.choice(names); s = random.choice([0, 1, 2, 3, 5, 5.5, 7, 7.0, -1])
        bd.set_score(n, s); ref[n] = s
    if random.random() < .3 and ref:
        n = random.choice(list(ref)); bd.remove(n); del ref[n]
    if not ref:
        continue
    order = sorted(ref.items(), key=lambda kv: (-kv[1], kv[0]))
    rows = [(1 + sum(1 for _, v in order if v > s), n, s) for n, s in order]
    assert bd.top(len(rows)) == rows
    size = random.randint(1, 7)
    pages = []
    p = 1
    while bd.page(p, size):
        pages += bd.page(p, size); p += 1
    assert pages == rows
    n = random.choice(list(ref)); k = random.randint(0, 4)
    i = [r[1] for r in rows].index(n)
    assert bd.around(n, k) == rows[max(0, i - k): i + k + 1]
    if len(ref) > 1:
        assert bd.percentile(n) == 100.0 * sum(1 for m, v in ref.items() if m != n and v < ref[n]) / (len(ref) - 1)
print("ok")
