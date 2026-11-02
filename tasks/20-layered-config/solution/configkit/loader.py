"""Load layered configuration with provenance."""
from .env import env_overrides
from .merge import merge


def _leaves(d, prefix=""):
    for k, v in d.items():
        path = prefix + k
        if isinstance(v, dict):
            yield from _leaves(v, path + ".")
        else:
            yield path


def _set_sources(prov, override, source, prefix=""):
    for k, v in override.items():
        path = prefix + k
        if v is None:
            for p in [p for p in prov if p == path or p.startswith(path + ".")]:
                del prov[p]
        elif isinstance(v, dict):
            # A dict replacing a non-dict leaf drops that leaf's entry.
            prov.pop(path, None)
            _set_sources(prov, v, source, path + ".")
        else:
            for p in [p for p in prov if p.startswith(path + ".")]:
                del prov[p]
            prov[path] = source


def load(defaults, layers=(), env=None, prefix="APP"):
    config = merge({}, defaults)
    prov = {}
    _set_sources(prov, defaults, "defaults")
    for name, mapping in layers:
        config = merge(config, mapping)
        _set_sources(prov, mapping, name)
    if env is not None:
        ov = env_overrides(env, prefix, defaults)
        config = merge(config, ov)
        _set_sources(prov, ov, "env")
    assert set(prov) == set(_leaves(config)), (prov, config)
    return config, prov
