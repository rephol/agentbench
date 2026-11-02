import unittest
from billing.invoice import line_text, total_text, balance_text


class InvoiceTest(unittest.TestCase):
    def test_line(self):
        self.assertEqual(line_text("Pen", 3, 1.5), "Pen x3 @ $1.50 = $4.50")

    def test_total(self):
        self.assertEqual(total_text([("a", 1, 1000), ("b", 2, 0.25)]), "TOTAL: $1,000.50")

    def test_balance_negative(self):
        self.assertEqual(balance_text(10, 12.5), "Due: -$2.50")
