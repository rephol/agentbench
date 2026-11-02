"""Money helpers. All amounts are integer cents."""


def split_cents(total, weights):
    """Split `total` cents across `weights` proportionally.

    Rules:
    * The parts are non-negative-weight proportional shares and MUST sum exactly to `total`.
    * Use the largest-remainder method: every part starts at floor(total * w / sum(w)),
      then the leftover cents go one each to the parts with the largest fractional
      remainders; ties go to the lower index.
    * Weights of 0 always get 0.
    * A negative `total` mirrors a positive one: split_cents(-x, w) == [-p for p in split_cents(x, w)].
    * Empty weights, a negative weight, or all-zero weights raise ValueError.
    * Weights may be ints only (no floats) and the result must be exact (no float math).
    """
    s = sum(weights)
    return [round(total * w / s) for w in weights]
