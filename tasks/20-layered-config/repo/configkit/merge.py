"""Layered dictionary merge."""


def merge(base, override):
    """Return a new dict: `base` overlaid with `override`.

    * Dicts merge recursively, key by key.
    * Any other value in `override` (including lists) replaces the one in `base`
      outright; lists are never concatenated.
    * A value of `None` in `override` DELETES that key from the result (at any depth); a
      `None` for a key that does not exist is ignored. A `None` inside a list is just a value.
    * Neither input is modified, and the result shares no mutable object (dict or list,
      at any depth) with either input: mutating the result later must not change them.
    * If `base[k]` is a dict and `override[k]` is not a dict (and not None), the override
      wins; if `base[k]` is not a dict and `override[k]` is a dict, the dict wins (with its
      own None entries dropped, since they delete nothing).
    """
    raise NotImplementedError
