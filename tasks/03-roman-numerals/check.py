import os, sys
sys.path.insert(0, os.getcwd())
from roman import to_roman
known = {1: "I", 4: "IV", 9: "IX", 14: "XIV", 40: "XL", 90: "XC", 400: "CD", 444: "CDXLIV",
         1994: "MCMXCIV", 2024: "MMXXIV", 3999: "MMMCMXCIX", 3888: "MMMDCCCLXXXVIII"}
for n, s in known.items():
    assert to_roman(n) == s, (n, to_roman(n), s)
vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
def back(s):
    t = 0
    for i, c in enumerate(s):
        v = vals[c]
        t += -v if i + 1 < len(s) and vals[s[i + 1]] > v else v
    return t
for n in range(1, 4000):
    assert back(to_roman(n)) == n, n
for bad in (0, -1, 4000):
    try:
        to_roman(bad); raise SystemExit("no ValueError for %r" % bad)
    except ValueError:
        pass
for bad in (1.5, "3", None, True):
    try:
        to_roman(bad); raise SystemExit("no TypeError for %r" % (bad,))
    except TypeError:
        pass
print("ok")
