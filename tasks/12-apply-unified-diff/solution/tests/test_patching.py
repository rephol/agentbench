import unittest
from patching import apply_patch, PatchError


class PatchTest(unittest.TestCase):
    def test_simple_replace(self):
        patch = "--- a\n+++ b\n@@ -1,3 +1,3 @@\n a\n-b\n+B\n c\n"
        self.assertEqual(apply_patch("a\nb\nc\n", patch), "a\nB\nc\n")

    def test_mismatch(self):
        with self.assertRaises(PatchError):
            apply_patch("x\n", "@@ -1 +1 @@\n-y\n+z\n")
