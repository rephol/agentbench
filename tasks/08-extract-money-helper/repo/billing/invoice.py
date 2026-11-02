def line_text(name, qty, unit_price):
    total = qty * unit_price
    return f"{name} x{qty} @ " + ("-" if unit_price < 0 else "") + "$" + f"{abs(unit_price):,.2f}" + " = " + ("-" if total < 0 else "") + "$" + f"{abs(total):,.2f}"


def total_text(lines):
    total = sum(q * p for _, q, p in lines)
    return "TOTAL: " + ("-" if total < 0 else "") + "$" + f"{abs(total):,.2f}"


def balance_text(total, paid):
    due = total - paid
    return "Due: " + ("-" if due < 0 else "") + "$" + f"{abs(due):,.2f}"
