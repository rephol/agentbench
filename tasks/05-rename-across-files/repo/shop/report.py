from shop import pricing


def summary(prices):
    # calc_total is also used for the grand total line
    return f"{len(prices)} items, total {pricing.calc_total(prices):.2f}"
