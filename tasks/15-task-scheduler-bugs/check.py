import os, sys
sys.path.insert(0, os.getcwd())
import subprocess, sys
from sched.planner import plan, critical_path, CycleError, UnknownDependency
def T(**kw): return {k: ({"duration": v[0], "deps": v[1]} if isinstance(v, tuple) else {"duration": v}) for k, v in kw.items()}
d = {"a": {"duration": 1}, "b": {"deps": ["a"], "duration": 1}, "c": {"deps": ["a"], "duration": 1}, "d": {"deps": ["b", "c"], "duration": 1}}
assert plan(d) == ["a", "b", "c", "d"]
assert plan({"z": {"duration": 1}, "m": {"deps": ["z"], "duration": 1}, "a": {"duration": 1}}) == ["a", "z", "m"]
assert plan({"b": {"duration": 1}, "a": {"deps": ["b"], "duration": 1}, "c": {"duration": 1}}) == ["b", "a", "c"]
assert plan({}) == []
# deps may be missing; duplicates in deps are fine
assert plan({"x": {"duration": 0}, "y": {"deps": ["x", "x"], "duration": 0}}) == ["x", "y"]
# cycles
for tasks, rem in [
    ({"a": {"deps": ["b"], "duration": 1}, "b": {"deps": ["a"], "duration": 1}, "c": {"deps": ["a"], "duration": 1}, "d": {"duration": 1}}, ["a", "b", "c"]),
    ({"a": {"deps": ["a"], "duration": 1}}, ["a"]),
    ({"x": {"duration": 1}, "a": {"deps": ["c"], "duration": 1}, "b": {"deps": ["a"], "duration": 1}, "c": {"deps": ["b"], "duration": 1}}, ["a", "b", "c"]),
]:
    try:
        plan(tasks); raise SystemExit("expected CycleError")
    except CycleError as e:
        assert e.remaining == rem, e.remaining
        assert isinstance(e, Exception)
try:
    critical_path({"a": {"deps": ["a"], "duration": 1}}); raise SystemExit("expected CycleError")
except CycleError:
    pass
# unknown dependency is reported before a cycle
try:
    plan({"a": {"deps": ["b"], "duration": 1}, "b": {"deps": ["a"], "duration": 1}, "c": {"deps": ["nope"], "duration": 1}})
    raise SystemExit("expected UnknownDependency")
except UnknownDependency:
    pass
try:
    critical_path({"a": {"deps": ["zzz"], "duration": 1}}); raise SystemExit("expected UnknownDependency")
except UnknownDependency:
    pass
assert issubclass(UnknownDependency, KeyError)
# critical path
t = {"a": {"duration": 2}, "b": {"deps": ["a"], "duration": 3}, "c": {"deps": ["a"], "duration": 1}, "d": {"deps": ["b", "c"], "duration": 4}}
assert critical_path(t) == (9, ["a", "b", "d"])
t["d"]["deps"] = ["c", "b"]
assert critical_path(t) == (9, ["a", "b", "d"]), "dependency order must not matter"
assert critical_path({}) == (0, [])
assert critical_path({"solo": {"duration": 5}}) == (5, ["solo"])
tie = {"x": {"duration": 3}, "y": {"duration": 3}, "end": {"deps": ["y", "x"], "duration": 1}}
assert critical_path(tie) == (4, ["x", "end"])
two = {"q": {"duration": 4}, "p": {"duration": 4}, "z": {"duration": 1}}
assert critical_path(two) == (4, ["p"])
mix = {"s": {"duration": 1}, "l": {"deps": ["s"], "duration": 10}, "m": {"deps": ["s"], "duration": 2}, "e": {"deps": ["l", "m"], "duration": 1}, "f": {"deps": ["m"], "duration": 1}}
assert critical_path(mix) == (12, ["s", "l", "e"])
r = subprocess.run([sys.executable, "-m", "unittest", "-q"], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
print("ok")
