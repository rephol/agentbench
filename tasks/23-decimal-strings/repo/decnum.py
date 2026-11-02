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


def normalize(a):
    raise NotImplementedError


def add(a, b):
    raise NotImplementedError


def sub(a, b):
    raise NotImplementedError


def mul(a, b):
    raise NotImplementedError


def cmp(a, b):
    raise NotImplementedError


def quantize(a, places, mode="half_even"):
    raise NotImplementedError


def div(a, b, places, mode="half_even"):
    raise NotImplementedError
