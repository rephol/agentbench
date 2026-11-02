"""Environment variable overrides."""


def env_overrides(env, prefix, schema):
    """Turn environment variables into a nested override dict.

    `env` maps variable names to strings. A variable is used only if its name starts with
    `prefix + "__"` (prefix match is case-sensitive; e.g. prefix "APP" uses `APP__DB__PORT`).
    The rest of the name, split on `__` and lowercased, is the key path:
    `APP__DB__PORT=5432` -> {"db": {"port": 5432}}.

    `schema` is the defaults dict; the type of the value found at the same path in
    `schema` decides how the string is converted:
    * bool: "true", "1", "yes", "on" -> True; "false", "0", "no", "off" -> False
      (case-insensitive, surrounding whitespace ignored); anything else raises ValueError.
      (Check bool before int: bool is a subclass of int.)
    * int: int(value) (ValueError propagates); float: float(value).
    * list: comma-separated; items are stripped; an empty string gives []; each item is
      converted like a scalar of the type of the schema list's first element if the schema
      list is non-empty, else left as str.
    * str, None, a path missing from the schema, or a schema value of any other type: the
      string unchanged.
    Empty path segments (`APP____X`, `APP__`) raise ValueError, as does a variable that
    would be both a leaf and a parent (`APP__DB=1` together with `APP__DB__PORT=2`).
    Variables without the prefix are ignored. Return {} when nothing matches. The input
    dicts are not modified.
    """
    raise NotImplementedError
