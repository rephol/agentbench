"""Load layered configuration with provenance."""


def load(defaults, layers=(), env=None, prefix="APP"):
    """Combine configuration sources.

    Order of precedence, lowest first: `defaults`, then each `(name, mapping)` in `layers`
    in order, then environment overrides (from `env`, a dict of strings, via
    `env_overrides` using `defaults` as the schema; skipped when env is None).
    Merging uses `merge` semantics (None deletes, lists replace).

    Returns `(config, provenance)`. `provenance` maps the dotted path of every LEAF in
    the final config to the name of the source that last set it: "defaults", the layer's
    name, or "env". A leaf is any non-dict value (lists are leaves). Dicts that end up empty
    contribute no entries. A key deleted by a later source disappears from both. If a source
    re-sets a leaf to the same value, it still becomes that leaf's source.
    Neither the config nor any source may alias the other (see `merge`).
    """
    raise NotImplementedError
