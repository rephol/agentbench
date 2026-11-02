import os, sys, random
sys.path.insert(0, os.getcwd())
from ledger import split_cents
from invoice import apply_discount
from statement import invoice_total

def raises(f, *a):
    try:
        f(*a)
    except ValueError:
        return True
    return False

assert split_cents(100, [1, 1, 1]) == [34, 33, 33]
assert split_cents(100, [1, 1]) == [50, 50]
assert split_cents(1, [1, 1, 1]) == [1, 0, 0]
assert split_cents(2, [1, 1, 1]) == [1, 1, 0]
assert split_cents(10, [3, 3, 4]) == [3, 3, 4]
assert split_cents(0, [1, 2]) == [0, 0]
assert split_cents(100, [0, 1, 0, 1]) == [0, 50, 0, 50]
assert split_cents(101, [0, 1, 0, 1]) == [0, 51, 0, 50]
assert split_cents(5, [1, 2, 2]) == [1, 2, 2]
assert split_cents(7, [5, 3, 3]) == [3, 2, 2]          # remainders .18, .09 ... checked below by oracle
assert split_cents(-100, [1, 1, 1]) == [-34, -33, -33]
assert split_cents(99, [1]) == [99]
big = 10 ** 30 + 7
parts = split_cents(big, [3, 5, 11])
assert sum(parts) == big and all(isinstance(p, int) for p in parts)
assert raises(split_cents, 5, []) and raises(split_cents, 5, [0, 0]) and raises(split_cents, 5, [1, -1])

random.seed(3)
for _ in range(2000):
    n = random.randint(1, 8)
    w = [random.choice([0, 0, 1, 2, 3, 7, 10, 99]) for _ in range(n)]
    if sum(w) == 0:
        w[0] = 1
    t = random.randint(-1000, 1000)
    got = split_cents(t, w)
    assert sum(got) == t, (t, w, got)
    # oracle: exact rationals
    from fractions import Fraction
    s = sum(w)
    a = abs(t)
    base = [a * x // s for x in w]
    rem = [Fraction(a * x, s) - b for x, b in zip(w, base)]
    left = a - sum(base)
    order = sorted(range(n), key=lambda i: (-rem[i], i))
    for i in order[:left]:
        base[i] += 1
    want = base if t >= 0 else [-x for x in base]
    assert got == want, (t, w, got, want)
    assert all(g == 0 for g, x in zip(got, w) if x == 0)

assert apply_discount([1000, 2000, 3000], 600) == [900, 1800, 2700]
assert apply_discount([100, 100, 100], 100) == [66, 67, 67] or apply_discount([100, 100, 100], 100) == [66, 67, 67]
assert apply_discount([100, 100, 100], 100) == [66, 67, 67]
assert apply_discount([5, 5], 1) == [4, 5]
assert apply_discount([5, 10], 0) == [5, 10]
assert apply_discount([5, 10], 15) == [0, 0]
assert apply_discount([1, 1, 1], 3) == [0, 0, 0]
assert apply_discount([0, 7, 0], 3) == [0, 4, 0]
lines = [333, 333, 334]
before = list(lines)
out = apply_discount(lines, 10)
assert lines == before and sum(out) == sum(lines) - 10 and all(0 <= o <= l for o, l in zip(out, lines))
assert raises(apply_discount, [5, 5], 11) and raises(apply_discount, [5, 5], -1) and raises(apply_discount, [5, -5], 1)
assert raises(apply_discount, [], 1) and raises(apply_discount, [0, 0], 1)
assert apply_discount([], 0) == []
assert invoice_total([1000, 2000, 3000], 601) == 6000 - 601
for _ in range(500):
    ls = [random.randint(0, 5000) for _ in range(random.randint(1, 6))]
    d = random.randint(0, sum(ls))
    o = apply_discount(ls, d)
    assert sum(o) == sum(ls) - d and all(0 <= x <= l for x, l in zip(o, ls)), (ls, d, o)
print("ok")
