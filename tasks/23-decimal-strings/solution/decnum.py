"""Exact decimal arithmetic on strings (no `decimal`, `fractions` or float).

All functions take and return decimal STRINGS.

Accepted input: optional sign (+ or -), digits with an optional single dot, at least one digit
overall: "12", "-3.50", "+.5", "5.", "007.100", "-0". No exponent, no whitespace, no
underscores, no "NaN"/"inf". Anything else raises ValueError.

Canonical output (every function returns this form): no leading zeros before the dot (except a
single "0"), no trailing zeros after the dot, no trailing dot, no "+" sign, and zero is "0"
(never "-0" or "0.0"). Examples: "007.100" -> "7.1", "-0.00" -> "0", "5." -> "5", "+.5" -> "0.5".

* normalize(a)                      -> canonical form of a
* add(a, b), sub(a, b), mul(a, b)   -> exact results
* cmp(a, b)                         -> -1, 0 or 1 (returns an int, compares numerically)
* quantize(a, places, mode="half_even") -> a rounded to `places` digits after the dot
  (places >= 0, else ValueError), then canonical (so trailing zeros are dropped).
  Modes use the same meaning as Python's decimal module rounding constants:
    "half_even"  nearest, ties to the even last digit
    "half_up"    nearest, ties away from zero
    "half_down"  nearest, ties toward zero
    "up"         away from zero      "down" toward zero (truncate)
    "floor"      toward -infinity    "ceil" toward +infinity
  An unknown mode raises ValueError. A result that rounds to zero is "0" (never "-0").
* div(a, b, places, mode="half_even")  -> a / b rounded to `places` digits like quantize,
  computed exactly (the rounding must look at the true quotient, not a truncated one).
  Division by zero raises ZeroDivisionError.
Values can have hundreds of digits; the result must be exact.
"""


import re

_RE = re.compile(r"^([+-]?)(\d*)(?:\.(\d*))?$")
_MODES = {"half_even", "half_up", "half_down", "up", "down", "floor", "ceil"}


def _parse(a):
    """Return (numerator_int, scale) such that value = numerator / 10**scale."""
    if not isinstance(a, str):
        raise ValueError("not a string")
    m = _RE.match(a)
    if not m or not (m.group(2) or m.group(3)):
        raise ValueError("bad decimal %r" % (a,))
    sign, ip, fp = m.group(1), m.group(2), m.group(3) or ""
    n = int((ip + fp) or "0")
    return (-n if sign == "-" else n), len(fp)


def _fmt(n, scale):
    neg = n < 0
    d = str(abs(n)).rjust(scale + 1, "0")
    ip, fp = (d[:-scale], d[-scale:]) if scale else (d, "")
    fp = fp.rstrip("0")
    s = ip + ("." + fp if fp else "")
    return "-" + s if neg and s != "0" else s


def _align(a, b):
    na, sa = _parse(a)
    nb, sb = _parse(b)
    s = max(sa, sb)
    return na * 10 ** (s - sa), nb * 10 ** (s - sb), s


def normalize(a):
    return _fmt(*_parse(a))


def add(a, b):
    x, y, s = _align(a, b)
    return _fmt(x + y, s)


def sub(a, b):
    x, y, s = _align(a, b)
    return _fmt(x - y, s)


def mul(a, b):
    na, sa = _parse(a)
    nb, sb = _parse(b)
    return _fmt(na * nb, sa + sb)


def cmp(a, b):
    x, y, _ = _align(a, b)
    return (x > y) - (x < y)


def _round_div(num, den, mode):
    """Round num/den (den > 0) to an integer under `mode`."""
    q, r = divmod(abs(num), den)
    neg = num < 0
    if r:
        twice = 2 * r
        if mode == "half_even":
            up = twice > den or (twice == den and q % 2 == 1)
        elif mode == "half_up":
            up = twice >= den
        elif mode == "half_down":
            up = twice > den
        elif mode == "up":
            up = True
        elif mode == "down":
            up = False
        elif mode == "floor":
            up = neg
        else:
            up = not neg
        if up:
            q += 1
    return -q if neg else q


def quantize(a, places, mode="half_even"):
    if mode not in _MODES:
        raise ValueError("bad mode")
    if not isinstance(places, int) or places < 0:
        raise ValueError("bad places")
    n, s = _parse(a)
    if s <= places:
        return _fmt(n, s)
    return _fmt(_round_div(n, 10 ** (s - places), mode), places)


def div(a, b, places, mode="half_even"):
    if mode not in _MODES:
        raise ValueError("bad mode")
    if not isinstance(places, int) or places < 0:
        raise ValueError("bad places")
    na, sa = _parse(a)
    nb, sb = _parse(b)
    if nb == 0:
        raise ZeroDivisionError
    # a/b = (na/10^sa) / (nb/10^sb); scaled by 10^places:
    num = na * 10 ** (places + sb)
    den = nb * 10 ** sa
    if den < 0:
        num, den = -num, -den
    return _fmt(_round_div(num, den, mode), places)
