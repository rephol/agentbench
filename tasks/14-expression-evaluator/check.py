import os, sys
sys.path.insert(0, os.getcwd())
import random, re
from calc import evaluate

src = open("calc.py").read()
for banned in (r"(?<![\w.])eval\s*\(", r"(?<![\w.])exec\s*\(", r"(?<![\w.])compile\s*\(", r"\bimport\s+ast\b", r"\bfrom\s+ast\b"):
    assert not re.search(banned, src), "banned construct: " + banned

def same(expr):
    try:
        want = eval(expr)
    except ArithmeticError as e:
        want = type(e)
    try:
        got = evaluate(expr)
    except ArithmeticError as e:
        got = type(e)
    assert got == want and type(got) is type(want), (expr, got, want)

for e in ["1", "1+2*3", "-2**2", "2**3**2", "2**-1", "-2**-2", "(1+2)*3", "10/4", "10//4", "-7//2", "-7%3", "7%-3",
          "1.5+.5", "2.", " 3 *  4 ", "--3", "+-+3", "2*-3", "4/2", "2**0", "0**0", "(2)", "((3))", "1-2-3", "8/4/2",
          "2**3*2", "-(2+3)**2", "2**(1+1)**2", "1e0"[:1], "100//7%5", "0.1+0.2", "7.5//2", "-7.5%2"]:
    same(e)
assert evaluate("4/2") == 2.0 and isinstance(evaluate("4/2"), float)
assert isinstance(evaluate("2+3"), int) and isinstance(evaluate("2.0+3"), float)
for e in ["1/0", "1//0", "1%0", "0**-1", "5/(2-2)"]:
    try:
        evaluate(e); raise SystemExit("expected ZeroDivisionError: " + e)
    except ZeroDivisionError:
        pass
for e in ["", "   ", "(", ")", "(1+2", "1+2)", "1+", "*2", "1 2", "1 + * 2", "2 ** ", "a", "1 + a", "()", "1..2", "3 $ 4", "1 +/ 2"]:
    try:
        evaluate(e); raise SystemExit("expected ValueError: %r" % e)
    except ValueError:
        pass
rnd = random.Random(2024)
def num():
    return rnd.choice([str(rnd.randint(0, 9)), str(rnd.randint(0, 99)), "%d.%d" % (rnd.randint(0, 9), rnd.randint(0, 99)), ".5"])
def gen(d):
    r = rnd.random()
    if d <= 0 or r < 0.2:
        return num()
    if r < 0.35:
        return rnd.choice(["-", "+"]) + gen(d - 1)
    if r < 0.5:
        return "(" + gen(d - 1) + ")"
    if r < 0.62:
        return "(" + gen(d - 1) + ")" + "**" + rnd.choice(["", "-", "+"]) + str(rnd.randint(0, 3))
    op = rnd.choice(["+", "-", "*", "/", "//", "%", "+", "-", "*"])
    return gen(d - 1) + rnd.choice(["", " "]) + op + rnd.choice(["", " "]) + gen(d - 1)
for _ in range(3000):
    e = gen(rnd.randint(1, 5))
    # keep the reference eval cheap and free of complex results
    if "**" in e and re.search(r"\d\.\d*\)?\*\*", e) and False:
        continue
    try:
        same(e)
    except SystemExit:
        raise
print("ok")
