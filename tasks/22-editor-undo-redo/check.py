import os, sys
sys.path.insert(0, os.getcwd())
from editor import Editor

def st(e):
    return (e.text, list(e.tags), dict(e.settings))

e = Editor("hello")
e.insert(5, " world")
e.delete(0, 1)
assert e.text == "ello world"
assert e.undo() and e.text == "hello world"
assert e.undo() and e.text == "hello"
assert not e.undo() and e.text == "hello"
assert e.redo() and e.text == "hello world" and e.redo() and e.text == "ello world" and not e.redo()

# redo is discarded by a new edit
e = Editor("a"); e.insert(1, "b"); e.insert(2, "c"); e.undo(); e.undo()
e.insert(1, "X")
assert e.text == "aX" and not e.redo()
assert e.undo() and e.text == "a" and not e.undo()

# no-ops record nothing
e = Editor("abc")
e.insert(1, ""); e.delete(1, 0); e.delete(3, 5); e.delete(0, -2); e.add_tag("t"); e.add_tag("t"); e.set_setting("k", 1); e.set_setting("k", 1)
assert e.undo() and e.settings == {} and e.undo() and e.tags == [] and not e.undo() and e.text == "abc"
for bad in [(-1, "x"), (4, "x")]:
    try:
        e.insert(*bad)
    except IndexError:
        pass
    else:
        raise SystemExit("expected IndexError")
try:
    e.delete(9, 1)
except IndexError:
    pass
else:
    raise SystemExit("expected IndexError")
e = Editor("ab"); e.insert(2, "c")
try: e.insert(99, "z")
except IndexError: pass
assert e.undo() and e.text == "ab" and not e.undo()   # failed call recorded nothing
e = Editor("abcdef"); e.delete(4, 100)
assert e.text == "abcd" and e.undo() and e.text == "abcdef"

# limit
e = Editor("", limit=3)
for ch in "abcde":
    e.insert(len(e.text), ch)
assert e.text == "abcde"
assert e.undo() and e.undo() and e.undo() and e.text == "ab" and not e.undo()
e = Editor("x", limit=0); e.insert(1, "y")
assert not e.undo() and e.text == "xy"
e = Editor("", limit=1); e.insert(0, "a"); e.insert(1, "b"); e.undo(); e.undo()
assert e.text == "a"

# nested mutable settings and aliasing
e = Editor()
lst = [1, 2]
e.set_setting("l", lst)
lst.append(3)
assert e.settings["l"] == [1, 2]
e.settings["l"].append(99)          # in-place mutation through the editor, NOT a recorded step
e.set_setting("n", {"a": [1]})
e.settings["n"]["a"].append(2)
e.set_setting("z", 1)
assert e.undo()
assert e.settings["n"] == {"a": [1, 2]} and e.settings["l"] == [1, 2, 99]
assert e.undo()
assert "n" not in e.settings and e.settings["l"] == [1, 2, 99]
assert e.redo() and e.settings["n"] == {"a": [1, 2]}
e.settings["n"]["a"].append(3)      # mutate after redo; undo again must not see a corrupted history
assert e.redo() and e.settings["z"] == 1
assert e.undo() and e.undo()
assert "n" not in e.settings
# snapshots are independent copies
e = Editor("t"); e.add_tag("x"); e.set_setting("d", {"k": [1]})
s = e.snapshot()
s["tags"].append("hack"); s["settings"]["d"]["k"].append(9); s["text"] = "no"
assert st(e) == ("t", ["x"], {"d": {"k": [1]}})
e.undo(); e.undo()
assert e.snapshot() == {"text": "t", "tags": [], "settings": {}}
e.redo(); e.redo()
assert e.snapshot() == {"text": "t", "tags": ["x"], "settings": {"d": {"k": [1]}}}
# tags: mutating the list after a step must not corrupt earlier snapshots
e = Editor(); e.add_tag("a"); e.add_tag("b"); e.undo()
assert e.tags == ["a"]; e.add_tag("c"); assert e.undo() and e.tags == ["a"] and e.undo() and e.tags == []

# groups
e = Editor("abc")
with e.group():
    e.insert(3, "d"); e.delete(0, 1); e.add_tag("g"); e.set_setting("s", [1])
assert st(e) == ("bcd", ["g"], {"s": [1]})
assert e.undo() and st(e) == ("abc", [], {}) and not e.undo()
assert e.redo() and st(e) == ("bcd", ["g"], {"s": [1]})
with e.group():
    pass
with e.group():
    e.insert(0, "")           # nothing changed
assert e.undo() and e.text == "abc"   # still just the one earlier step
e = Editor("a")
with e.group():
    e.insert(1, "b")
    with e.group():
        e.insert(2, "c")
    e.insert(3, "d")
assert e.text == "abcd" and e.undo() and e.text == "a" and not e.undo()
# exceptions roll back
e = Editor("a"); e.insert(1, "b"); e.undo()                  # redo available
try:
    with e.group():
        e.insert(1, "X"); e.add_tag("t")
        raise RuntimeError("boom")
except RuntimeError:
    pass
assert st(e) == ("a", [], {}) and e.redo() and e.text == "ab" and e.undo() and e.text == "a"
e = Editor("a")
try:
    with e.group():
        e.insert(1, "X")
        with e.group():
            e.insert(2, "Y")
            raise ValueError
except ValueError:
    pass
assert e.text == "a" and not e.undo()
# nested group exception caught inside the outer group: outer still commits what was done
e = Editor("a")
with e.group():
    e.insert(1, "b")
    try:
        with e.group():
            e.insert(2, "c")
            raise KeyError
    except KeyError:
        pass
assert e.text == "abc" and e.undo() and e.text == "a"
# group counts as one step against limit
e = Editor("", limit=2)
with e.group():
    e.insert(0, "a"); e.insert(1, "b")
e.insert(2, "c"); e.insert(3, "d")
assert e.undo() and e.undo() and e.text == "ab" and not e.undo()
print("ok")
