"""A tiny text editor model with undo/redo.

State is `text` (str), `tags` (list of str) and `settings` (dict of str -> any JSON-like
value, including nested lists/dicts).

Required behaviour:

* insert(pos, s): insert `s` at index `pos`. `pos` must satisfy 0 <= pos <= len(text) else
  IndexError (state and history untouched). Inserting "" changes nothing and records nothing.
* delete(pos, n): remove up to `n` characters starting at `pos` (clamped to the end of the text).
  Same IndexError rule for `pos`; n <= 0 or an empty clamped range changes nothing and records nothing.
* add_tag(tag): append the tag if it is not already present (else a no-op, nothing recorded).
* set_setting(key, value): set a setting; setting a key to a value equal to its current value
  is a no-op (nothing recorded). `value` may be a list/dict: the editor must keep its own copy,
  so later changes to the caller's object do not affect the editor or its history.
* Every state-changing call above is one undoable step.
* undo() -> bool: restore the state from before the latest step; returns False (and does
  nothing) if there is nothing to undo. redo() -> bool: re-apply the latest undone step; False
  if there is nothing to redo. A new state-changing call after undo() discards the redo steps.
* `limit` (constructor argument, default 100) is the maximum number of undoable steps kept:
  when a new step would exceed it, the OLDEST step is forgotten. limit=0 means nothing is
  undoable. Redo steps are not limited separately (they come from undone steps).
* `with editor.group():` makes everything inside ONE undo step. Groups nest: only the
  outermost group counts, and an inner group never creates its own step. A group in which
  nothing changed records nothing. If the body raises, the state is rolled back to what it was when
  the outermost group started, no step is recorded (redo steps are left as they were), and the
  exception propagates.
* snapshot() returns a fully independent deep copy: {"text", "tags", "settings"}. Mutating a
  snapshot (or anything returned from .tags / .settings after the fact) must never change the
  editor's history; undo/redo must restore exactly the earlier values, including nested
  list/dict settings that were mutated in place through `editor.settings`.
"""
from history import History
from contextlib import contextmanager


class Editor:
    def __init__(self, text="", limit=100):
        self.text = text
        self.tags = []
        self.settings = {}
        self.history = History(limit)

    def snapshot(self):
        return {"text": self.text, "tags": self.tags, "settings": self.settings}

    def _restore(self, snap):
        self.text = snap["text"]
        self.tags = snap["tags"]
        self.settings = snap["settings"]

    def insert(self, pos, s):
        self.history.record(self.snapshot())
        self.text = self.text[:pos] + s + self.text[pos:]

    def delete(self, pos, n):
        self.history.record(self.snapshot())
        self.text = self.text[:pos] + self.text[pos + n:]

    def add_tag(self, tag):
        self.history.record(self.snapshot())
        self.tags.append(tag)

    def set_setting(self, key, value):
        self.history.record(self.snapshot())
        self.settings[key] = value

    def undo(self):
        snap = self.history.undo(self.snapshot())
        if snap is None:
            return False
        self._restore(snap)
        return True

    def redo(self):
        snap = self.history.redo(self.snapshot())
        if snap is None:
            return False
        self._restore(snap)
        return True

    @contextmanager
    def group(self):
        yield
