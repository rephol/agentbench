from billing.money import format_money


def line_text(name, qty, unit_price):
    total = qty * unit_price
    return f"{name} x{qty} @ " + format_money(unit_price) + " = " + format_money(total)


def total_text(lines):
    total = sum(q * p for _, q, p in lines)
    return "TOTAL: " + format_money(total)


def balance_text(total, paid):
    due = total - paid
    return "Due: " + format_money(due)
