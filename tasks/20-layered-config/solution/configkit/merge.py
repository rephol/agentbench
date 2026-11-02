"""Layered dictionary merge."""
import copy


def merge(base, override):
    out = copy.deepcopy(base)
    _apply(out, override)
    return out


def _clean(v):
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items() if x is not None}
    return copy.deepcopy(v)


def _apply(out, override):
    for k, v in override.items():
        if v is None:
            out.pop(k, None)
        elif isinstance(v, dict):
            if isinstance(out.get(k), dict):
                _apply(out[k], v)
            else:
                out[k] = _clean(v)
        else:
            out[k] = copy.deepcopy(v)
