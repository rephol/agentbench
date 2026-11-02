"""Slicing helpers used by the leaderboard."""


def paginate(rows, number, size):
    if number < 1 or size < 1:
        raise ValueError("page and size must be >= 1")
    start = (number - 1) * size
    return rows[start:start + size]


def slice_window(rows, idx, k):
    return rows[max(0, idx - k):idx + k + 1]
