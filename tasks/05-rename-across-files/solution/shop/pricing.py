def compute_total(prices, tax_rate=0.0):
    """Sum `prices` and add tax."""
    return round(sum(prices) * (1 + tax_rate), 2)
