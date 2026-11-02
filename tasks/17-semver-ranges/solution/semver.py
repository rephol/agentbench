"""npm-style semantic version ranges.

satisfies(version, range_expr) -> bool

`version` is "MAJOR.MINOR.PATCH" with an optional "-prerelease" and optional
"+build" (build metadata is ignored everywhere). A version string that is not
exactly that shape (e.g. "1.2", "v1.2.3", "01.2.3") raises ValueError.

Range grammar (same meaning as npm's `semver`, includePrerelease = false):

* A range is one or more comparator sets joined by `||`; a version satisfies the
  range if it satisfies any set. A set is whitespace-separated terms that must
  ALL hold. An empty set (or `*`) matches any non-prerelease version.
* Plain comparators: `>=1.2.3`, `>1.2.3`, `<=1.2.3`, `<1.2.3`, `=1.2.3`, `1.2.3`.
  Whitespace may separate the operator from the version (`>= 1.2.3`).
* Partial versions and x-ranges: a missing part or `x`, `X`, `*` is a wildcard.
  `1` = `1.x` = `>=1.0.0 <2.0.0`; `1.2` = `1.2.x` = `>=1.2.0 <1.3.0`.
  With operators: `>=1.2` = `>=1.2.0`; `>1.2` = `>=1.3.0`; `<=1.2` = `<1.3.0`;
  `<1.2` = `<1.2.0`; `>1` = `>=2.0.0`; `<=1` = `<2.0.0`; `=1.2` = `1.2.x`.
* Tilde: `~1.2.3` = `>=1.2.3 <1.3.0`; `~1.2` = `>=1.2.0 <1.3.0`;
  `~1` = `>=1.0.0 <2.0.0`; `~1.2.3-beta.2` = `>=1.2.3-beta.2 <1.3.0`.
* Caret (changes that do not modify the left-most non-zero part):
  `^1.2.3` = `>=1.2.3 <2.0.0`; `^0.2.3` = `>=0.2.3 <0.3.0`;
  `^0.0.3` = `>=0.0.3 <0.0.4`; `^1.2.x` = `>=1.2.0 <2.0.0`; `^0.0.x` = `>=0.0.0 <0.1.0`;
  `^0.0` = `>=0.0.0 <0.1.0`; `^1.x` = `>=1.0.0 <2.0.0`; `^0.x` = `>=0.0.0 <1.0.0`;
  `^1.2.3-beta.2` = `>=1.2.3-beta.2 <2.0.0`.
* Hyphen ranges: `1.2.3 - 2.3.4` = `>=1.2.3 <=2.3.4`. A partial lower bound is
  zero-filled (`1.2 - 2.3.4` = `>=1.2.0 <=2.3.4`); a partial upper bound includes
  the whole partial (`1.2.3 - 2.3` = `>=1.2.3 <2.4.0`, `1.2.3 - 2` = `>=1.2.3 <3.0.0`).
* Ordering follows semver 2.0: compare major, minor, patch numerically; a version
  with a prerelease is lower than the same version without; prerelease
  identifiers compare left to right, numeric ones numerically and lower than
  alphanumeric ones, alphanumeric ones in ASCII order, and a shorter list is
  lower when all its identifiers equal the longer one's prefix.
* Prerelease rule: a version that has a prerelease can satisfy a comparator set
  only if at least one comparator in that SAME set has a prerelease and the same
  major.minor.patch tuple as the version. So `1.2.3-beta.4` satisfies
  `^1.2.3-beta.2` but not `^1.2.0`, and `1.2.4-beta.1` does not satisfy
  `^1.2.3-beta.2`.
* An unparseable range raises ValueError.
"""


import re

_VER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")
_PART = re.compile(r"^(?:v|=)?(x|X|\*|\d+)(?:\.(x|X|\*|\d+))?(?:\.(x|X|\*|\d+))?(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z.-]+)?$")


def parse(v):
    m = _VER.match(v)
    if not m:
        raise ValueError("bad version %r" % (v,))
    pre = tuple(m.group(4).split(".")) if m.group(4) else ()
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), pre)


def _idkey(i):
    return (0, int(i), "") if i.isdigit() else (1, 0, i)


def cmp(a, b):
    ta, tb = a[:3], b[:3]
    if ta != tb:
        return -1 if ta < tb else 1
    pa, pb = a[3], b[3]
    if not pa and not pb:
        return 0
    if not pa:
        return 1
    if not pb:
        return -1
    ka, kb = [_idkey(i) for i in pa], [_idkey(i) for i in pb]
    return 0 if ka == kb else (-1 if ka < kb else 1)


def _partial(s):
    m = _PART.match(s)
    if not m:
        raise ValueError("bad range term %r" % (s,))
    nums = []
    for g in m.groups()[:3]:
        nums.append(None if g is None or g in "xX*" else int(g))
    # Once a wildcard appears, everything after it is a wildcard too.
    for i in range(3):
        if nums[i] is None:
            nums[i:] = [None] * (3 - i)
            break
    pre = tuple(m.group(4).split(".")) if m.group(4) else ()
    if pre and None in nums:
        raise ValueError("prerelease on partial version")
    return nums, pre


def _v(M, m, p, pre=()):
    return (M, m, p, pre)


def _xrange(op, s):
    (M, m, p), pre = _partial(s)[0], _partial(s)[1]
    if op in ("", "="):
        if M is None:
            return []
        if m is None:
            return [(">=", _v(M, 0, 0)), ("<", _v(M + 1, 0, 0))]
        if p is None:
            return [(">=", _v(M, m, 0)), ("<", _v(M, m + 1, 0))]
        return [("=", _v(M, m, p, pre))]
    if op == ">":
        if M is None:
            return [("<", _v(0, 0, 0))]
        if m is None:
            return [(">=", _v(M + 1, 0, 0))]
        if p is None:
            return [(">=", _v(M, m + 1, 0))]
        return [(">", _v(M, m, p, pre))]
    if op == ">=":
        return [(">=", _v(M or 0, m or 0, p or 0, pre))] if M is not None else []
    if op == "<":
        return [("<", _v(M or 0, m or 0, p or 0, pre))] if M is not None else [("<", _v(0, 0, 0))]
    if op == "<=":
        if M is None:
            return []
        if m is None:
            return [("<", _v(M + 1, 0, 0))]
        if p is None:
            return [("<", _v(M, m + 1, 0))]
        return [("<=", _v(M, m, p, pre))]
    raise ValueError(op)


def _tilde(s):
    (M, m, p), pre = _partial(s)
    if M is None:
        return []
    if m is None:
        return [(">=", _v(M, 0, 0)), ("<", _v(M + 1, 0, 0))]
    if p is None:
        return [(">=", _v(M, m, 0)), ("<", _v(M, m + 1, 0))]
    return [(">=", _v(M, m, p, pre)), ("<", _v(M, m + 1, 0))]


def _caret(s):
    (M, m, p), pre = _partial(s)
    if M is None:
        return []
    if m is None:
        return [(">=", _v(M, 0, 0)), ("<", _v(M + 1, 0, 0))]
    if p is None:
        if M == 0:
            return [(">=", _v(0, m, 0)), ("<", _v(0, m + 1, 0))]
        return [(">=", _v(M, m, 0)), ("<", _v(M + 1, 0, 0))]
    lo = (">=", _v(M, m, p, pre))
    if M > 0:
        return [lo, ("<", _v(M + 1, 0, 0))]
    if m > 0:
        return [lo, ("<", _v(0, m + 1, 0))]
    return [lo, ("<", _v(0, 0, p + 1))]


def _hyphen(a, b):
    (M, m, p), pre = _partial(a)
    lo = [] if M is None else [(">=", _v(M, m or 0, p or 0, pre))]
    (M2, m2, p2), pre2 = _partial(b)
    if M2 is None:
        hi = []
    elif m2 is None:
        hi = [("<", _v(M2 + 1, 0, 0))]
    elif p2 is None:
        hi = [("<", _v(M2, m2 + 1, 0))]
    else:
        hi = [("<=", _v(M2, m2, p2, pre2))]
    return lo + hi


def _test(v, op, t):
    c = cmp(v, t)
    return {"=": c == 0, ">": c > 0, ">=": c >= 0, "<": c < 0, "<=": c <= 0}[op]


def _set(expr):
    expr = re.sub(r"(>=|<=|>|<|=|\^|~)\s+", r"\1", expr.strip())
    toks = expr.split()
    comps = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if i + 2 < len(toks) + 0 and toks[i + 1] == "-":
            comps += _hyphen(t, toks[i + 2])
            i += 3
            continue
        m = re.match(r"^(>=|<=|>|<|=|\^|~)?(.*)$", t)
        op, rest = m.group(1) or "", m.group(2)
        if not rest:
            raise ValueError("bad range term %r" % (t,))
        if op == "^":
            comps += _caret(rest)
        elif op == "~":
            comps += _tilde(rest)
        else:
            comps += _xrange(op, rest)
        i += 1
    return comps


def satisfies(version, range_expr):
    v = parse(version)
    for part in range_expr.split("||"):
        comps = _set(part)
        if not all(_test(v, op, t) for op, t in comps):
            continue
        if v[3] and not any(t[3] and t[:3] == v[:3] for _, t in comps):
            continue
        return True
    return False
