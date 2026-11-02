"""Undo/redo history."""


class History:
    def __init__(self, limit):
        self.limit = max(0, limit)
        self.undo_stack = []
        self.redo_stack = []

    def record(self, state):
        """Remember `state` (the state BEFORE a new step) as undoable."""
        self.redo_stack.clear()
        if self.limit == 0:
            return
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.limit:
            self.undo_stack.pop(0)

    def undo(self, current):
        if not self.undo_stack:
            return None
        self.redo_stack.append(current)
        return self.undo_stack.pop()

    def redo(self, current):
        if not self.redo_stack:
            return None
        self.undo_stack.append(current)
        return self.redo_stack.pop()
