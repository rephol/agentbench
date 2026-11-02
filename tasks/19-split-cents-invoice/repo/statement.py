"""Statement totals (uses the other modules)."""
from invoice import apply_discount


def invoice_total(lines, discount=0):
    return sum(apply_discount(lines, discount))
