from shop import pricing


def summary(prices):
    # compute_total is also used for the grand total line
    return f"{len(prices)} items, total {pricing.compute_total(prices):.2f}"
