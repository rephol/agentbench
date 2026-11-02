import unittest
from calc import evaluate


class CalcTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(evaluate("1 + 2 * 3"), 7)

    def test_power(self):
        self.assertEqual(evaluate("-2**2"), -4)
        self.assertEqual(evaluate("2**3**2"), 512)

    def test_errors(self):
        with self.assertRaises(ValueError):
            evaluate("(1 + 2")
        with self.assertRaises(ZeroDivisionError):
            evaluate("1 / 0")
