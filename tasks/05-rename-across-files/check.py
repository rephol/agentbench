import os, sys
sys.path.insert(0, os.getcwd())
import os, subprocess, sys
for root, _, files in os.walk("."):
    for f in files:
        if f.endswith(".py") and f != "check.py":
            assert "calc_total" not in open(os.path.join(root, f)).read(), os.path.join(root, f)
from shop.pricing import compute_total
from shop.cart import Cart
from shop.report import summary
assert compute_total([1, 2, 3], 0.1) == 6.6
c = Cart(); c.add(10); c.add(5)
assert c.total() == 15 and c.total(0.2) == 18.0
assert summary([1, 2]) == "2 items, total 3.00"
r = subprocess.run([sys.executable, "-m", "unittest", "-q"], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
assert "compute_total" in open("tests/test_shop.py").read()
print("ok")
