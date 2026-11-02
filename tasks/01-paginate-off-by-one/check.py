import os, sys
sys.path.insert(0, os.getcwd())
from pager import paginate, page_count
items = list(range(10))
assert paginate(items, 1, 3) == [0, 1, 2], paginate(items, 1, 3)
assert paginate(items, 2, 3) == [3, 4, 5]
assert paginate(items, 4, 3) == [9]
assert paginate(items, 5, 3) == []
assert paginate([], 1, 5) == []
assert paginate(items, 1, 10) == items
assert page_count(10, 3) == 4 and page_count(9, 3) == 3
print("ok")
