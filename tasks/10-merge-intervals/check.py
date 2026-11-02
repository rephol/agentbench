import os, sys
sys.path.insert(0, os.getcwd())
import random
from intervals import merge_intervals as m
assert m([]) == []
assert m([(1, 3), (2, 6), (8, 10), (15, 18)]) == [(1, 6), (8, 10), (15, 18)]
assert m([(1, 4), (4, 5)]) == [(1, 5)]
assert m([[5, 6], [1, 2], [2, 3]]) == [(1, 3), (5, 6)]
assert m([(1, 10), (2, 3), (4, 5)]) == [(1, 10)]
assert m([(2, 2), (2, 2)]) == [(2, 2)] and m([(1, 1), (3, 3)]) == [(1, 1), (3, 3)]
assert m([(0.5, 1.5), (1.5, 2.0)]) == [(0.5, 2.0)]
src = [[3, 4], [1, 2]]
m(src)
assert src == [[3, 4], [1, 2]]
assert all(isinstance(x, tuple) for x in m([[1, 2]]))
try:
    m([(3, 1)]); raise SystemExit("expected ValueError")
except ValueError:
    pass
random.seed(7)
for _ in range(300):
    ivs = []
    for _ in range(random.randint(0, 12)):
        a = random.randint(0, 30); ivs.append((a, a + random.randint(0, 6)))
    pts = set()
    for s, e in ivs:
        pts.update(range(s, e + 1))
    out = m(ivs)
    cov = set()
    for s, e in out:
        cov.update(range(s, e + 1))
    assert cov == pts, (ivs, out)
    for (s1, e1), (s2, e2) in zip(out, out[1:]):
        assert e1 < s2, (ivs, out)
print("ok")
