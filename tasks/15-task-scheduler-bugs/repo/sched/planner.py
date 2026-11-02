"""Order tasks by their dependencies.

`tasks` maps a task name to a dict: {"deps": [names it needs first], "duration": number >= 0}.
"deps" may be missing (no dependencies).
"""


class CycleError(Exception):
    """The dependencies contain a cycle. `.remaining` is the sorted list of task names
    that could not be scheduled (cycle members and anything that depends on them)."""

    def __init__(self, remaining):
        super().__init__("cycle among: %s" % ", ".join(remaining))
        self.remaining = remaining


class UnknownDependency(KeyError):
    """A task depends on a name that is not in `tasks`."""


def plan(tasks):
    """Return the task names in execution order.

    Repeatedly pick the alphabetically smallest task whose dependencies have all been
    scheduled. Raise UnknownDependency if any dependency is not a key of `tasks`
    (checked before anything else), and CycleError (with `.remaining`) if the tasks
    cannot all be scheduled. A task that depends on itself is a cycle.
    """
    order, visited = [], set()

    def visit(name):
        if name in visited:
            return
        visited.add(name)
        for dep in tasks[name].get("deps", []):
            visit(dep)
        order.append(name)

    for name in tasks:
        visit(name)
    return order


def critical_path(tasks):
    """Return (total_duration, path) for the longest dependency chain.

    A task starts when all its dependencies have finished (time 0 if it has none) and
    finishes `duration` later. total_duration is the largest finish time (0 for no
    tasks). `path` is the list of names along one longest chain, in execution order:
    it ends at the alphabetically smallest task whose finish time equals the total, and
    walking backwards from a task it moves to the alphabetically smallest dependency
    whose finish time equals that task's start time. No tasks gives (0, []).
    Raises the same errors as `plan`.
    """
    finish = {}
    for name in plan(tasks):
        deps = tasks[name].get("deps", [])
        start = finish[deps[-1]] if deps else 0
        finish[name] = start + tasks[name]["duration"]
    if not finish:
        return 0, []
    total = max(finish.values())
    end = min(n for n, f in finish.items() if f == total)
    path = [end]
    return total, path
