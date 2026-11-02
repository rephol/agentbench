import os, random, sys
sys.path.insert(0, os.getcwd())
from datetime import datetime, timedelta
from cron import next_fire

D = datetime
cases = [
 ("* * * * *", D(2024, 1, 1, 12, 0, 30), D(2024, 1, 1, 12, 1)),
 ("* * * * *", D(2024, 1, 1, 12, 0, 0), D(2024, 1, 1, 12, 1)),
 ("*/15 * * * *", D(2024, 1, 1, 12, 15), D(2024, 1, 1, 12, 30)),
 ("*/15 * * * *", D(2024, 1, 1, 12, 45), D(2024, 1, 1, 13, 0)),
 ("0 0 * * *", D(2024, 12, 31, 23, 59), D(2025, 1, 1, 0, 0)),
 ("30 9 * * mon-fri", D(2024, 6, 7, 9, 30), D(2024, 6, 10, 9, 30)),   # Fri -> Mon
 ("30 9 * * 1-5", D(2024, 6, 8, 0, 0), D(2024, 6, 10, 9, 30)),        # Sat
 ("0 12 * * 0", D(2024, 6, 9, 12, 0), D(2024, 6, 16, 12, 0)),
 ("0 12 * * 7", D(2024, 6, 9, 12, 0), D(2024, 6, 16, 12, 0)),
 ("0 12 * * SUN", D(2024, 6, 10, 0, 0), D(2024, 6, 16, 12, 0)),
 ("0 0 29 2 *", D(2024, 3, 1), D(2028, 2, 29, 0, 0)),
 ("0 0 29 2 *", D(2096, 3, 1), D(2104, 2, 29, 0, 0)),           # skips non-leap 2100
 ("0 0 31 * *", D(2024, 4, 1), D(2024, 5, 31, 0, 0)),
 ("0 0 31 * *", D(2024, 1, 31, 0, 0), D(2024, 3, 31, 0, 0)),
 ("0 0 30 * *", D(2023, 1, 30, 0, 0), D(2023, 3, 30, 0, 0)),
 ("0 0 1,15 * *", D(2024, 1, 15, 0, 0), D(2024, 2, 1, 0, 0)),
 ("5 4 * jan,jul *", D(2024, 2, 1), D(2024, 7, 1, 4, 5)),
 ("5 4 * 1-3 *", D(2024, 3, 31, 5, 0), D(2025, 1, 1, 4, 5)),
 ("0 0 13 * fri", D(2024, 1, 1), D(2024, 1, 5, 0, 0)),          # dom OR dow
 ("0 0 13 * fri", D(2024, 1, 6), D(2024, 1, 12, 0, 0)),
 ("0 0 13 * fri", D(2024, 1, 12, 0, 0), D(2024, 1, 13, 0, 0)),
 ("0 0 */2 * fri", D(2024, 1, 2, 0, 0), D(2024, 1, 3, 0, 0)),   # */2 dom is unrestricted -> only fri? no
 ("0 0 1 * *", D(2024, 1, 1, 0, 0), D(2024, 2, 1, 0, 0)),
 ("10-20/5 1,2 * * *", D(2024, 1, 1, 1, 10), D(2024, 1, 1, 1, 15)),
 ("10-20/5 1,2 * * *", D(2024, 1, 1, 1, 20), D(2024, 1, 1, 2, 10)),
 ("10-20/5 1,2 * * *", D(2024, 1, 1, 2, 20), D(2024, 1, 2, 1, 10)),
 ("45/5 * * * *", D(2024, 1, 1, 0, 45), D(2024, 1, 1, 0, 50)),
 ("45/5 * * * *", D(2024, 1, 1, 0, 59), D(2024, 1, 1, 1, 45)),
 ("0 0 * * mon-sun/3", D(2024, 6, 9), D(2024, 6, 10, 0, 0)),
 ("0\t0  1 JAN *", D(2024, 1, 1, 0, 0), D(2025, 1, 1, 0, 0)),
 ("59 23 31 12 *", D(2024, 12, 31, 23, 58, 59, 999), D(2024, 12, 31, 23, 59)),
]
# The "*/2 dom with fri dow" case: dom text starts with '*', so only the dow is used.
cases[21] = ("0 0 */2 * fri", D(2024, 1, 2, 0, 0), D(2024, 1, 5, 0, 0))
for expr, after, want in cases:
    got = next_fire(expr, after)
    assert got == want, (expr, after, want, got)
    assert got.second == 0 and got.microsecond == 0

for bad in ["* * * *", "* * * * * *", "60 * * * *", "* 24 * * *", "* * 0 * *", "* * 32 * *", "* * * 13 *", "* * * * 8",
            "*/0 * * * *", "5-1 * * * *", "* * * * fri-mon", "* * * foo *", ", * * * *", "1,,2 * * * *", "a * * * *",
            "-1 * * * *", "*/x * * * *", "0 0 30 2 *", "0 0 31 4,6,9,11 *"]:
    try:
        next_fire(bad, D(2024, 1, 1))
    except ValueError:
        continue
    raise SystemExit("expected ValueError for %r" % (bad,))

# Cross-check against minute-by-minute scanning.
def fields(expr):
    names_m = {"jan": 1, "feb": 2, "mar": 3}
    p = expr.split()
    def rng(t, lo, hi):
        s = set()
        for it in t.split(","):
            b, _, st = it.partition("/")
            st = int(st) if st else 1
            if b == "*": a, z = lo, hi
            elif "-" in b: a, z = map(int, b.split("-"))
            else: a = int(b); z = hi if "/" in it else a
            s.update(range(a, z + 1, st))
        return s
    return rng(p[0], 0, 59), rng(p[1], 0, 23), rng(p[2], 1, 31), rng(p[3], 1, 12), {x % 7 for x in rng(p[4], 0, 7)}, p[2][0] != "*", p[4][0] != "*"

def brute(expr, after):
    mi, ho, dm, mo, dw, dr, wr = fields(expr)
    t = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(60 * 24 * 400):
        ok = t.minute in mi and t.hour in ho and t.month in mo
        a, b = t.day in dm, (t.isoweekday() % 7) in dw
        ok = ok and ((a or b) if dr and wr else a if dr else b if wr else True)
        if ok:
            return t
        t += timedelta(minutes=1)
    raise AssertionError

random.seed(11)
pieces = lambda lo, hi: random.choice(["*", "*/%d" % random.randint(2, 7), str(random.randint(lo, hi)), "%d-%d" % (lo, lo + (hi - lo) // 2),
                                       "%d,%d" % (random.randint(lo, hi), random.randint(lo, hi)), "%d-%d/%d" % (lo, hi, random.randint(2, 5))])
for _ in range(60):
    expr = " ".join([pieces(0, 59), pieces(0, 23), pieces(1, 28), "*" if random.random() < .5 else "1-12", pieces(0, 6) if random.random() < .5 else "*"])
    after = D(2024, random.randint(1, 12), random.randint(1, 28), random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))
    try:
        want = brute(expr, after)
    except AssertionError:
        continue
    assert next_fire(expr, after) == want, (expr, after, want, next_fire(expr, after))
print("ok")
