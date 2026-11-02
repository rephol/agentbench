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
import copy
from contextlib import contextmanager

from history import History


class Editor:
    def __init__(self, text="", limit=100):
        self.text = text
        self.tags = []
        self.settings = {}
        self.history = History(limit)
        self._depth = 0
        self._group_start = None
        self._group_changed = False

    def snapshot(self):
        return copy.deepcopy({"text": self.text, "tags": self.tags, "settings": self.settings})

    def _restore(self, snap):
        snap = copy.deepcopy(snap)
        self.text = snap["text"]
        self.tags = snap["tags"]
        self.settings = snap["settings"]

    def _step(self):
        """Call before mutating: records a step unless inside a group."""
        if self._depth:
            if self._group_start is None:
                self._group_start = self.snapshot()
            return
        self.history.record(self.snapshot())

    def insert(self, pos, s):
        if not 0 <= pos <= len(self.text):
            raise IndexError(pos)
        if not s:
            return
        self._step()
        self.text = self.text[:pos] + s + self.text[pos:]

    def delete(self, pos, n):
        if not 0 <= pos <= len(self.text):
            raise IndexError(pos)
        n = min(n, len(self.text) - pos)
        if n <= 0:
            return
        self._step()
        self.text = self.text[:pos] + self.text[pos + n:]

    def add_tag(self, tag):
        if tag in self.tags:
            return
        self._step()
        self.tags.append(tag)

    def set_setting(self, key, value):
        if key in self.settings and self.settings[key] == value:
            return
        self._step()
        self.settings[key] = copy.deepcopy(value)

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
        outer = self._depth == 0
        if outer:
            self._group_start = None
        self._depth += 1
        try:
            yield
        except BaseException:
            self._depth -= 1
            if outer:
                if self._group_start is not None:
                    self._restore(self._group_start)
                self._group_start = None
            raise
        else:
            self._depth -= 1
            if outer:
                start, self._group_start = self._group_start, None
                if start is not None:
                    self.history.record(start)
