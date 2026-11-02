def format_money(amount):
    """Format a number as dollars with thousands separators; negatives get a leading '-'."""
    return ("-" if amount < 0 else "") + "$" + f"{abs(amount):,.2f}"
