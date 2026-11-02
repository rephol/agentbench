def merge_intervals(intervals):
    """Merge overlapping intervals.

    `intervals` is an iterable of (start, end) pairs (tuples or lists) of numbers.
    Return a new list of (start, end) tuples sorted by start, in which every group
    of intervals that overlap OR touch (one's end equals the next's start) is
    merged into one. The input must not be mutated. Empty input returns [].
    An interval with start > end raises ValueError. Zero-length intervals
    (start == end) are valid.
    """
    raise NotImplementedError
