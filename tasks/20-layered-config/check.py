import copy, os, sys
sys.path.insert(0, os.getcwd())
from configkit import merge, env_overrides, load

def raises(f, *a, **k):
    try:
        f(*a, **k)
    except ValueError:
        return True
    return False

# ---- merge
assert merge({"a": 1, "b": {"c": 2, "d": 3}}, {"b": {"c": 9}, "e": 5}) == {"a": 1, "b": {"c": 9, "d": 3}, "e": 5}
assert merge({"l": [1, 2]}, {"l": [3]}) == {"l": [3]}
assert merge({"a": 1, "b": 2}, {"a": None}) == {"b": 2}
assert merge({"a": {"b": 1, "c": 2}}, {"a": {"b": None}}) == {"a": {"c": 2}}
assert merge({}, {"x": None}) == {}
assert merge({"a": {"b": {"c": 1}}}, {"a": {"b": None}}) == {"a": {}}
assert merge({"a": 1}, {"a": {"b": 2, "z": None}}) == {"a": {"b": 2}}
assert merge({"a": {"b": 1}}, {"a": 5}) == {"a": 5}
assert merge({"a": [1, None]}, {}) == {"a": [1, None]}
assert merge({}, {"a": {"b": {"c": None, "d": 1}}}) == {"a": {"b": {"d": 1}}}
b = {"a": {"l": [1, [2]]}, "k": [{"x": 1}]}
o = {"z": {"m": [3]}, "a": {"q": [4]}}
bb, oo = copy.deepcopy(b), copy.deepcopy(o)
r = merge(b, o)
assert b == bb and o == oo
r["a"]["l"][1].append(99); r["k"][0]["x"] = 7; r["z"]["m"].append(5); r["a"]["q"].append(6)
assert b == bb and o == oo, "result aliases an input"
r2 = merge(b, {})
r2["a"]["l"].append(0)
assert b == bb

# ---- env
S = {"db": {"port": 5432, "host": "x", "ssl": False}, "debug": False, "ratio": 0.5, "tags": ["a"], "ports": [1], "name": None,
     "n": {"deep": {"v": 1}}}
E = lambda env: env_overrides(env, "APP", S)
assert E({}) == {} and E({"OTHER__X": "1", "APPX__Y": "1", "app__db__port": "1"}) == {}
assert E({"APP__DB__PORT": "6000"}) == {"db": {"port": 6000}}
assert E({"APP__DB__SSL": " Yes "}) == {"db": {"ssl": True}}
assert E({"APP__DEBUG": "0"}) == {"debug": False} and E({"APP__DEBUG": "ON"}) == {"debug": True}
assert E({"APP__RATIO": "0.25"}) == {"ratio": 0.25} and isinstance(E({"APP__RATIO": "1"})["ratio"], float)
assert E({"APP__TAGS": "x, y ,z"}) == {"tags": ["x", "y", "z"]}
assert E({"APP__TAGS": ""}) == {"tags": []}
assert E({"APP__PORTS": "1, 2,3"}) == {"ports": [1, 2, 3]}
assert E({"APP__NAME": "bob"}) == {"name": "bob"}
assert E({"APP__NEW__THING": "5"}) == {"new": {"thing": "5"}}
assert E({"APP__N__DEEP__V": "7", "APP__DB__HOST": "h"}) == {"n": {"deep": {"v": 7}}, "db": {"host": "h"}}
assert E({"APP__DB": "x"}) == {"db": "x"}
assert env_overrides({"X__A": "1"}, "X", {}) == {"a": "1"}
assert env_overrides({"APP__Mixed__Case": "1"}, "APP", {"mixed": {"case": 5}}) == {"mixed": {"case": 1}}
assert raises(E, {"APP__DEBUG": "maybe"}) and raises(E, {"APP__DB__PORT": "abc"}) and raises(E, {"APP__PORTS": "1,x"})
assert raises(E, {"APP____X": "1"}) and raises(E, {"APP__": "1"}) and raises(E, {"APP__A__": "1"})
assert raises(E, {"APP__DB": "1", "APP__DB__PORT": "2"})
sch = copy.deepcopy(S)
E({"APP__DB__PORT": "1"})
assert S == sch

# ---- load
D = {"db": {"host": "localhost", "port": 5432}, "debug": False, "tags": ["a", "b"], "old": 1}
L1 = ("file", {"db": {"port": 6000}, "extra": {"k": 1}})
L2 = ("local", {"old": None, "tags": ["z"], "db": {"host": "h2"}})
cfg, prov = load(D, [L1, L2], env={"APP__DEBUG": "true", "APP__DB__PORT": "7000"})
assert cfg == {"db": {"host": "h2", "port": 7000}, "debug": True, "tags": ["z"], "extra": {"k": 1}}
assert prov == {"db.host": "local", "db.port": "env", "debug": "env", "tags": "local", "extra.k": "file"}, prov
cfg, prov = load(D)
assert cfg == D and prov == {"db.host": "defaults", "db.port": "defaults", "debug": "defaults", "tags": "defaults", "old": "defaults"}
cfg, prov = load(D, [("a", {"db": None})])
assert cfg == {"debug": False, "tags": ["a", "b"], "old": 1} and "db.host" not in prov and prov["old"] == "defaults"
cfg, prov = load(D, [("a", {"db": None}), ("b", {"db": {"port": 1}})])
assert cfg["db"] == {"port": 1} and prov["db.port"] == "b" and "db.host" not in prov
cfg, prov = load(D, [("same", {"debug": False})])
assert prov["debug"] == "same"
cfg, prov = load({"a": 1}, [("l", {"a": {"b": 2}})])
assert cfg == {"a": {"b": 2}} and prov == {"a.b": "l"}
cfg, prov = load({"a": {"b": 2}}, [("l", {"a": 7})])
assert cfg == {"a": 7} and prov == {"a": "l"}
cfg, prov = load({"e": {}}, [])
assert cfg == {"e": {}} and prov == {}
cfg, prov = load(D, env={"OTHER": "1"}, prefix="APP")
assert prov["db.port"] == "defaults"
cfg, prov = load(D, env={"MY__DEBUG": "1"}, prefix="MY")
assert cfg["debug"] is True and prov["debug"] == "env"
dd = copy.deepcopy(D)
cfg, _ = load(D, [("x", {"tags": ["q"]})])
cfg["db"]["host"] = "mutated"; cfg["tags"].append("m")
assert D == dd
l = [1]
cfg, _ = load({"t": l}, [])
cfg["t"].append(2)
assert l == [1]
print("ok")
