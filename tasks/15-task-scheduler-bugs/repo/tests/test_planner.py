import unittest
from sched.planner import plan, critical_path, CycleError


class PlannerTest(unittest.TestCase):
    def test_diamond(self):
        tasks = {"a": {"duration": 1}, "b": {"deps": ["a"], "duration": 1},
                 "c": {"deps": ["a"], "duration": 1}, "d": {"deps": ["b", "c"], "duration": 1}}
        self.assertEqual(plan(tasks), ["a", "b", "c", "d"])

    def test_cycle(self):
        with self.assertRaises(CycleError):
            plan({"a": {"deps": ["b"], "duration": 1}, "b": {"deps": ["a"], "duration": 1}})

    def test_critical_path(self):
        tasks = {"a": {"duration": 2}, "b": {"deps": ["a"], "duration": 3},
                 "c": {"deps": ["a"], "duration": 1}, "d": {"deps": ["b", "c"], "duration": 4}}
        self.assertEqual(critical_path(tasks), (9, ["a", "b", "d"]))
