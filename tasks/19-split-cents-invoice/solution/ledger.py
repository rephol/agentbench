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
    if not weights or any(w < 0 for w in weights) or sum(weights) == 0:
        raise ValueError("bad weights")
    if total < 0:
        return [-p for p in split_cents(-total, weights)]
    s = sum(weights)
    parts = [total * w // s for w in weights]
    rems = [(total * w) % s for w in weights]
    left = total - sum(parts)
    order = sorted(range(len(weights)), key=lambda i: (-rems[i], i))
    for i in order[:left]:
        parts[i] += 1
    return parts
