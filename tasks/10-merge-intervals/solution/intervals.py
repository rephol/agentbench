def merge_intervals(intervals):
    """Merge overlapping or touching intervals; see task statement."""
    pairs = []
    for iv in intervals:
        s, e = iv
        if s > e:
            raise ValueError("start > end: %r" % (iv,))
        pairs.append((s, e))
    pairs.sort()
    out = []
    for s, e in pairs:
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out
