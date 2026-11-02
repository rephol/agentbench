def paginate(items, page, per_page):
    """Return the items on the 1-indexed `page`.

    Pages hold `per_page` items each; the last page may be shorter.
    A page past the end returns an empty list.
    """
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end]


def page_count(total, per_page):
    """Number of pages needed for `total` items."""
    return -(-total // per_page)
