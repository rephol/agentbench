import os, sys
sys.path.insert(0, os.getcwd())
import subprocess, sys, hashlib
from textutil import slugify
cases = {"Hello, World!": "hello-world", "  a  b ": "a-b", "foo--bar": "foo-bar",
         "C++ rocks": "c-rocks", "": "", "---": "", "Already-slug": "already-slug", "a1 b2": "a1-b2"}
for k, v in cases.items():
    assert slugify(k) == v, (k, slugify(k), v)
r = subprocess.run([sys.executable, "-m", "unittest", "-q"], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
src = open("tests/test_textutil.py").read()
assert 'slugify("Hello, World!"), "hello-world"' in src and 'slugify("  a  b "), "a-b"' in src, "tests were edited"
print("ok")
