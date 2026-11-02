import os, sys
sys.path.insert(0, os.getcwd())
import subprocess, sys
from billing.money import format_money
from billing.invoice import line_text, total_text, balance_text
assert format_money(0) == "$0.00" and format_money(1234567.891) == "$1,234,567.89"
assert format_money(-0.5) == "-$0.50" and format_money(-1000) == "-$1,000.00"
assert line_text("Pen", 3, 1.5) == "Pen x3 @ $1.50 = $4.50"
assert line_text("Refund", 2, -1200) == "Refund x2 @ -$1,200.00 = -$2,400.00"
assert total_text([("a", 1, 1000), ("b", 2, 0.25)]) == "TOTAL: $1,000.50"
assert balance_text(10, 12.5) == "Due: -$2.50" and balance_text(2000, 0) == "Due: $2,000.00"
src = open("billing/invoice.py").read()
assert ":,.2f" not in src, "formatting still duplicated in invoice.py"
assert "format_money" in src
r = subprocess.run([sys.executable, "-m", "unittest", "-q"], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
print("ok")
