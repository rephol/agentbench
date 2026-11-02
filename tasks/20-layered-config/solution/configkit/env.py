"""Environment variable overrides."""

_TRUE = {"true", "1", "yes", "on"}
_FALSE = {"false", "0", "no", "off"}


def _scalar(s, like):
    if isinstance(like, bool):
        t = s.strip().lower()
        if t in _TRUE:
            return True
        if t in _FALSE:
            return False
        raise ValueError("bad bool %r" % (s,))
    if isinstance(like, int):
        return int(s)
    if isinstance(like, float):
        return float(s)
    return s


def _convert(s, like):
    if isinstance(like, list):
        if s == "":
            return []
        proto = like[0] if like else ""
        return [_scalar(x.strip(), proto) for x in s.split(",")]
    return _scalar(s, like)


def env_overrides(env, prefix, schema):
    out = {}
    head = prefix + "__"
    for name in sorted(env):
        if not name.startswith(head):
            continue
        path = name[len(head):].lower().split("__")
        if any(p == "" for p in path):
            raise ValueError("empty path segment in %s" % name)
        like = schema
        for p in path:
            like = like.get(p) if isinstance(like, dict) else None
        node = out
        for p in path[:-1]:
            nxt = node.setdefault(p, {})
            if not isinstance(nxt, dict):
                raise ValueError("conflict at %s" % name)
            node = nxt
        if path[-1] in node:
            raise ValueError("conflict at %s" % name)
        node[path[-1]] = _convert(env[name], like)
    return out
