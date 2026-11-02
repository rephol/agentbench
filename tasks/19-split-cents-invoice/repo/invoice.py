"""Invoice helpers."""
from ledger import split_cents


def apply_discount(lines, discount):
    """Spread `discount` cents across invoice `lines` (a list of line amounts in cents).

    The discount is shared proportionally to each line's amount (use `split_cents`), so the
    total discount is exactly `discount`. A line's discount can never exceed its amount.
    Returns the list of discounted line amounts (amount - share), same order as `lines`.

    * discount == 0 returns the lines unchanged.
    * A discount larger than the sum of the lines raises ValueError; so does a negative
      discount, a negative line, or an empty / all-zero list with a non-zero discount.
    * The input list is not modified.
    """
    total = sum(lines)
    out = []
    for amount in lines:
        share = round(discount * amount / total)
        out.append(amount - share)
    return out
