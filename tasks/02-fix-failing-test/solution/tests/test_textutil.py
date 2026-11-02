import unittest
from textutil import slugify


class SlugifyTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_punctuation(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_extra_spaces(self):
        self.assertEqual(slugify("  a  b "), "a-b")


if __name__ == "__main__":
    unittest.main()
