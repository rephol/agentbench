import unittest
from shop.pricing import compute_total
from shop.cart import Cart
from shop.report import summary


class ShopTest(unittest.TestCase):
    def test_compute_total(self):
        self.assertEqual(compute_total([1, 2, 3], 0.1), 6.6)

    def test_cart(self):
        c = Cart()
        c.add(10)
        c.add(5)
        self.assertEqual(c.total(), 15)

    def test_summary(self):
        self.assertEqual(summary([1, 2]), "2 items, total 3.00")
