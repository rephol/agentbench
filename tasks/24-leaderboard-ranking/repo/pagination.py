"""Slicing helpers used by the leaderboard."""


def paginate(rows, number, size):
    start = number * size
    return rows[start:start + size]


def slice_window(rows, idx, k):
    return rows[max(0, idx - k):idx + k]
