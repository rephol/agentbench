_TABLE = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
          (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def to_roman(n):
    """Convert an integer 1..3999 to a Roman numeral string.

    Uses standard subtractive notation (4 -> "IV", 9 -> "IX", 40 -> "XL",
    90 -> "XC", 400 -> "CD", 900 -> "CM"). Raises ValueError for integers
    outside 1..3999 and TypeError for non-integers (bool counts as non-integer).
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")
    if not 1 <= n <= 3999:
        raise ValueError("n out of range")
    out = []
    for value, sym in _TABLE:
        while n >= value:
            out.append(sym)
            n -= value
    return "".join(out)
