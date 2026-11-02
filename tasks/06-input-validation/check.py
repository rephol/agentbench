import os, sys
sys.path.insert(0, os.getcwd())
from users import create_user
assert create_user("  Ann ", " Ann@Example.COM ", 30) == {"name": "Ann", "email": "ann@example.com", "age": 30}
assert create_user("B", "b@x.io", 0)["age"] == 0 and create_user("B", "b@x.io", 150)["age"] == 150
bad = [("", "a@b.co", 1), ("   ", "a@b.co", 1), (None, "a@b.co", 1), (5, "a@b.co", 1),
       ("A", "ab.co", 1), ("A", "@b.co", 1), ("A", "a@", 1), ("A", "a@@b.co", 1), ("A", "a@b@c.co", 1),
       ("A", "a@bco", 1), ("A", "a@.co", 1), ("A", "a@b.", 1), ("A", None, 1), ("A", 12, 1),
       ("A", "a@b.co", -1), ("A", "a@b.co", 151), ("A", "a@b.co", 3.5), ("A", "a@b.co", "3"),
       ("A", "a@b.co", True), ("A", "a@b.co", None)]
for args in bad:
    try:
        create_user(*args)
    except ValueError:
        continue
    raise SystemExit("expected ValueError for %r" % (args,))
print("ok")
