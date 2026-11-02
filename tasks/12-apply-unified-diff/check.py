import os, sys
sys.path.insert(0, os.getcwd())
import difflib, random
from patching import apply_patch, PatchError

def diff(a, b, n=3):
    al, bl = a.splitlines(keepends=True), b.splitlines(keepends=True)
    return "".join(difflib.unified_diff(al, bl, "a/f", "b/f", n=n))

# explicit cases
assert apply_patch("a\nb\nc\n", "--- a\n+++ b\n@@ -1,3 +1,3 @@\n a\n-b\n+B\n c\n") == "a\nB\nc\n"
assert apply_patch("anything\n", "") == "anything\n"
assert apply_patch("", "@@ -0,0 +1,2 @@\n+a\n+b\n") == "a\nb\n"
assert apply_patch("a\n", "@@ -1 +0,0 @@\n-a\n") == ""
assert apply_patch("a\nb\n", "@@ -1 +1 @@ ctx text\n-a\n+z\n") == "z\nb\n"
assert apply_patch("a\nb\n", "@@ -2,0 +3 @@\n+c\n") == "a\nb\nc\n"
assert apply_patch("a\nb\n", "@@ -0,0 +1 @@\n+first\n") == "first\na\nb\n"
# empty context line written as a bare empty line
assert apply_patch("a\n\nb\n", "@@ -1,3 +1,3 @@\n a\n\n-b\n+c\n") == "a\n\nc\n"
# no newline at end of file
NN = "\\ No newline at end of file\n"
assert apply_patch("a\nb", "@@ -1,2 +1,2 @@\n a\n-b\n" + NN + "+c\n" + NN) == "a\nc"
assert apply_patch("a", "@@ -1 +1 @@\n-a\n" + NN + "+a\n") == "a\n"
assert apply_patch("a\n", "@@ -1 +1,2 @@\n a\n+b\n" + NN) == "a\nb"
assert apply_patch("a\nb", "@@ -1,2 +1,3 @@\n a\n-b\n" + NN + "+b\n+c\n" + NN) == "a\nb\nc"
assert apply_patch("a\nb", "@@ -2 +2 @@\n-b\n" + NN + "+b\n") == "a\nb\n"
# two hunks
text = "".join("line%d\n" % i for i in range(1, 21))
p = "@@ -2,3 +2,2 @@\n line2\n-line3\n line4\n@@ -18,3 +17,4 @@\n line18\n line19\n+extra\n line20\n"
exp = text.replace("line3\n", "").replace("line19\n", "line19\nextra\n")
assert apply_patch(text, p) == exp
# failures
def fails(orig, patch):
    try:
        apply_patch(orig, patch)
    except PatchError:
        return True
    return False
assert fails("x\n", "@@ -1 +1 @@\n-y\n+z\n")
assert fails("x\ny\n", "@@ -1,2 +1,2 @@\n x\n-z\n+w\n")
assert fails("x", "@@ -1 +1 @@\n-x\n+y\n"), "old line has no newline but patch says it does"
assert fails("x\n", "@@ -1 +1 @@\n-x\n" + NN + "+y\n"), "old line has a newline but patch says not"
assert fails("a\nb\n", "@@ -1,2 +1,2 @@\n a\n-b\n")  # truncated: new count not met
assert fails("a\n", "@@ -1 +1 @@\n-a\n+b\n@@ -1 +1 @@\n-b\n+c\n"), "overlapping/out-of-order hunks"
assert fails("a\n", "@@ -5 +5 @@\n-a\n+b\n")
assert fails("a\n", "@@ nonsense @@\n-a\n")
# round trip against difflib on random texts
words = ["alpha", "beta", "", "gamma", "delta", "x", "y y", "  indented", "-dash", "+plus", "@@ at", "end"]
for seed in range(300):
    rnd = random.Random(seed)
    a = [rnd.choice(words) + "\n" for _ in range(rnd.randint(0, 25))]
    b = list(a)
    for _ in range(rnd.randint(0, 6)):
        op = rnd.choice("ird")
        if op == "i" or not b:
            b.insert(rnd.randint(0, len(b)), rnd.choice(words) + "\n")
        elif op == "r":
            b[rnd.randrange(len(b))] = rnd.choice(words) + "\n"
        else:
            del b[rnd.randrange(len(b))]
    A, B = "".join(a), "".join(b)
    for n in (0, 1, 3):
        got = apply_patch(A, diff(A, B, n))
        assert got == B, (seed, n)
print("ok")
