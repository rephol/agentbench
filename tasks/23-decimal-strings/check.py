import os, random, sys
sys.path.insert(0, os.getcwd())
import decnum as d
from decimal import Decimal, localcontext, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_UP, ROUND_DOWN, ROUND_FLOOR, ROUND_CEILING

src = open("decnum.py").read()
import re
assert not re.search(r"^\s*(import|from)\s+(decimal|fractions)\b", src, re.M), "forbidden module"

def raises(exc, f, *a):
    try:
        f(*a)
    except exc:
        return True
    return False

for s, want in [("12", "12"), ("-3.50", "-3.5"), ("+.5", "0.5"), ("5.", "5"), ("007.100", "7.1"), ("-0", "0"), ("-0.00", "0"),
                ("0.000", "0"), ("-.0", "0"), ("100", "100"), ("100.0", "100"), ("0.10", "0.1"), ("-007", "-7"), ("+0", "0"), ("1.0001", "1.0001")]:
    assert d.normalize(s) == want, (s, d.normalize(s), want)
for bad in ["", ".", "+", "-", "1e3", " 1", "1 ", "1_0", "NaN", "inf", "1.2.3", "--1", "+-1", "a", "1,5", "-.", "0x10"]:
    for f in (d.normalize,):
        assert raises(ValueError, f, bad), bad
assert raises(ValueError, d.add, "1", "x") and raises(ValueError, d.cmp, "", "1") and raises(ValueError, d.mul, "1", "1e1")

assert d.add("0.1", "0.2") == "0.3" and d.add("-1.5", "1.5") == "0" and d.add("999.999", "0.001") == "1000"
assert d.sub("1", "1.000") == "0" and d.sub("0", "0.5") == "-0.5" and d.sub("-2", "-3") == "1"
assert d.mul("-0", "5") == "0" and d.mul("-1.5", "-2") == "3" and d.mul("0.01", "0.01") == "0.0001" and d.mul("12345678901234567890", "98765432109876543210") == "1219326311370217952237463801111263526900"
assert d.cmp("1.0", "1") == 0 and d.cmp("-0", "0") == 0 and d.cmp("-1", "-2") == 1 and d.cmp("0.1", "0.09") == 1 and d.cmp("9", "10") == -1
assert type(d.cmp("1", "2")) is int

modes = {"half_even": ROUND_HALF_EVEN, "half_up": ROUND_HALF_UP, "half_down": ROUND_HALF_DOWN, "up": ROUND_UP,
         "down": ROUND_DOWN, "floor": ROUND_FLOOR, "ceil": ROUND_CEILING}
def canon(x):
    s = format(x, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
def q_ref(a, places, mode):
    with localcontext() as c:
        c.prec = 2000
        return canon(Decimal(a).quantize(Decimal(1).scaleb(-places), rounding=modes[mode]))
def div_ref(a, b, places, mode):
    with localcontext() as c:
        c.prec = 4000
        return canon((Decimal(a) / Decimal(b)).quantize(Decimal(1).scaleb(-places), rounding=modes[mode]))

for a, p, m, want in [("2.5", 0, "half_even", "2"), ("3.5", 0, "half_even", "4"), ("2.5", 0, "half_up", "3"), ("-2.5", 0, "half_up", "-3"),
                      ("-2.5", 0, "half_down", "-2"), ("2.6", 0, "half_down", "3"), ("-0.4", 0, "floor", "-1"), ("-0.4", 0, "ceil", "0"),
                      ("0.4", 0, "up", "1"), ("-0.4", 0, "down", "0"), ("1.2345", 2, "half_even", "1.23"), ("1.235", 2, "half_even", "1.24"),
                      ("1.2350000001", 2, "half_even", "1.24"), ("1.2349999999", 2, "half_up", "1.23"), ("5", 3, "up", "5"), ("-0.001", 2, "floor", "-0.01"),
                      ("-0.001", 2, "half_up", "0"), ("0.005", 2, "half_even", "0"), ("0.015", 2, "half_even", "0.02"), ("999.995", 2, "half_up", "1000")]:
    assert d.quantize(a, p, m) == want, (a, p, m, d.quantize(a, p, m), want)
assert d.quantize("2.5", 0) == "2"
assert raises(ValueError, d.quantize, "1", -1) and raises(ValueError, d.quantize, "1", 2, "bankers") and raises(ValueError, d.div, "1", "2", 1, "nope")
assert d.div("1", "3", 5) == "0.33333" and d.div("2", "3", 5) == "0.66667" and d.div("-1", "3", 2) == "-0.33" and d.div("1", "-3", 2) == "-0.33"
assert d.div("1", "8", 2, "half_even") == "0.12" and d.div("1", "8", 2, "half_up") == "0.13" and d.div("1", "8", 3) == "0.125"
assert d.div("10", "4", 0, "half_even") == "2" and d.div("10", "4", 0, "ceil") == "3" and d.div("-10", "4", 0, "floor") == "-3"
assert d.div("0", "-5", 3) == "0" and d.div("-0.0001", "10", 2) == "0" and d.div("0.5", "0.25", 0) == "2"
assert d.div("1", "3", 0, "up") == "1" and d.div("-1", "3", 0, "up") == "-1" and d.div("-1", "3", 0, "ceil") == "0"
assert raises(ZeroDivisionError, d.div, "1", "0.000", 2) and raises(ZeroDivisionError, d.div, "0", "-0", 2)

random.seed(9)
def rnd():
    ip = "".join(random.choice("0123456789") for _ in range(random.choice([0, 1, 1, 2, 5, 40, 150])))
    fp = "".join(random.choice("0123456789" if random.random() < .7 else "05") for _ in range(random.choice([0, 1, 2, 3, 10, 60])))
    if not ip and not fp:
        ip = "0"
    return random.choice(["", "-", "+"]) + ip + ("." + fp if fp or random.random() < .3 else "")
for _ in range(1500):
    a, b = rnd(), rnd()
    A, B = Decimal(a), Decimal(b)
    with localcontext() as c:
        c.prec = 3000
        assert d.add(a, b) == canon(A + B), (a, b)
        assert d.sub(a, b) == canon(A - B), (a, b)
        assert d.mul(a, b) == canon(A * B), (a, b)
    assert d.cmp(a, b) == (A > B) - (A < B), (a, b)
    assert d.normalize(a) == canon(A), a
    p = random.choice([0, 1, 2, 3, 5, 12])
    m = random.choice(list(modes))
    assert d.quantize(a, p, m) == q_ref(a, p, m), (a, p, m, d.quantize(a, p, m), q_ref(a, p, m))
    if B != 0:
        assert d.div(a, b, p, m) == div_ref(a, b, p, m), (a, b, p, m, d.div(a, b, p, m), div_ref(a, b, p, m))
# exact ties produced by division
for a, b, p in [("1", "8", 2), ("3", "8", 2), ("5", "2", 0), ("7", "2", 0), ("-5", "2", 0), ("1", "16", 3), ("25", "1000", 1)]:
    for m in modes:
        assert d.div(a, b, p, m) == div_ref(a, b, p, m), (a, b, p, m)
print("ok")
