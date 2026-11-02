import os, sys
sys.path.insert(0, os.getcwd())
from semver import satisfies

T = [
 # plain and partial
 ("1.2.3", "1.2.3", True), ("1.2.4", "1.2.3", False), ("1.2.3", "=1.2.3", True), ("1.2.3+build.5", "1.2.3", True),
 ("1.2.3", "", True), ("1.2.3", "*", True), ("0.0.0", "x", True), ("1.2.3", ">=1.2.3", True), ("1.2.3", ">1.2.3", False),
 ("1.2.3", "<=1.2.3", True), ("1.2.3", "<1.2.3", False), ("1.2.3", ">= 1.2.3", True), ("1.2.3", ">=1.2.0 <1.3.0", True),
 ("1.3.0", ">=1.2.0 <1.3.0", False),
 ("1.9.9", "1", True), ("2.0.0", "1", False), ("1.2.9", "1.2", True), ("1.3.0", "1.2", False), ("1.2.3", "1.x", True),
 ("1.2.3", "1.2.x", True), ("1.3.0", "1.2.*", False), ("1.2.0", ">=1.2", True), ("1.1.9", ">=1.2", False),
 ("1.2.9", ">1.2", False), ("1.3.0", ">1.2", True), ("1.2.9", "<=1.2", True), ("1.3.0", "<=1.2", False),
 ("1.1.9", "<1.2", True), ("1.2.0", "<1.2", False), ("2.0.0", ">1", True), ("1.9.9", ">1", False), ("1.9.9", "<=1", True),
 ("2.0.0", "<=1", False), ("1.2.5", "=1.2", True),
 # tilde
 ("1.2.3", "~1.2.3", True), ("1.2.9", "~1.2.3", True), ("1.3.0", "~1.2.3", False), ("1.2.2", "~1.2.3", False),
 ("1.2.0", "~1.2", True), ("1.3.0", "~1.2", False), ("1.9.0", "~1", True), ("2.0.0", "~1", False),
 ("0.2.9", "~0.2.3", True), ("0.3.0", "~0.2.3", False), ("0.9.0", "~0", True), ("1.0.0", "~0", False),
 # caret
 ("1.9.9", "^1.2.3", True), ("2.0.0", "^1.2.3", False), ("1.2.2", "^1.2.3", False),
 ("0.2.9", "^0.2.3", True), ("0.3.0", "^0.2.3", False), ("0.2.2", "^0.2.3", False),
 ("0.0.3", "^0.0.3", True), ("0.0.4", "^0.0.3", False), ("0.0.2", "^0.0.3", False),
 ("1.2.0", "^1.2.x", True), ("1.9.0", "^1.2.x", True), ("2.0.0", "^1.2.x", False),
 ("0.0.9", "^0.0.x", True), ("0.1.0", "^0.0.x", False), ("0.0.9", "^0.0", True), ("0.1.0", "^0.0", False),
 ("1.9.9", "^1.x", True), ("0.9.9", "^0.x", True), ("1.0.0", "^0.x", False), ("5.0.0", "^*", True), ("0.5.0", "^0", True),
 ("1.0.0", "^0", False), ("1.2.3", "^ 1.2.3", True),
 # hyphen
 ("1.2.3", "1.2.3 - 2.3.4", True), ("2.3.4", "1.2.3 - 2.3.4", True), ("2.3.5", "1.2.3 - 2.3.4", False), ("1.2.2", "1.2.3 - 2.3.4", False),
 ("1.2.0", "1.2 - 2.3.4", True), ("1.1.9", "1.2 - 2.3.4", False), ("2.3.9", "1.2.3 - 2.3", True), ("2.4.0", "1.2.3 - 2.3", False),
 ("2.9.9", "1.2.3 - 2", True), ("3.0.0", "1.2.3 - 2", False), ("0.0.1", "* - 2", True),
 # or
 ("1.0.0", "1.0.0 || 2.0.0", True), ("2.0.0", "1.0.0 || 2.0.0", True), ("3.0.0", "1.0.0 || 2.0.0", False),
 ("1.5.0", "<1.0.0 || >=1.2.0 <2.0.0", True), ("1.1.0", "<1.0.0 || >=1.2.0 <2.0.0", False), ("1.0.0", "|| 1.0.0", True),
 ("3.0.0", "^1.0.0 || ^2.0.0 || ^3.0.0", True), ("1.0.0", "1.0.0 ||", True),
 # prerelease rule
 ("1.2.3-beta.4", "^1.2.3-beta.2", True), ("1.2.3-beta.1", "^1.2.3-beta.2", False), ("1.2.3", "^1.2.3-beta.2", True),
 ("1.2.4-beta.1", "^1.2.3-beta.2", False), ("1.2.3-beta.4", "^1.2.0", False), ("1.2.3-beta.4", "*", False),
 ("1.2.3-beta.4", ">=1.2.3-alpha", True), ("1.2.4-alpha", ">=1.2.3-alpha", False), ("1.2.3-alpha", ">=1.2.3-beta", False),
 ("2.0.0-rc.1", "<2.0.0", False), ("2.0.0-rc.1", "<=2.0.0-rc.2", True), ("2.0.0-rc.3", "<=2.0.0-rc.2", False),
 ("1.0.0-alpha", "1.0.0-alpha", True), ("1.0.0-alpha", "1.0.0", False), ("1.0.0", "1.0.0-alpha", False),
 ("1.2.3-beta.4", "~1.2.3-beta.2", True), ("1.2.4", "~1.2.3-beta.2", True), ("1.2.3-beta.4", "~1.2.3-beta.2 || 5", True),
 ("1.0.0-beta", "1.0.0-alpha || 1.0.0-beta", True), ("1.0.0-beta", "1.0.0-alpha || >=1.0.0", False),
 ("1.0.0-alpha.1", ">1.0.0-alpha", True), ("1.0.0-alpha.beta", ">1.0.0-alpha.1", True), ("1.0.0-alpha.1", "<1.0.0-alpha.beta", True),
 ("1.0.0-beta.11", ">1.0.0-beta.2", True), ("1.0.0-beta.2", "<1.0.0-beta.11", True), ("1.0.0-rc.1", ">1.0.0-beta.11", True),
 ("1.0.0-alpha", ">=1.0.0-alpha.0", False), ("1.0.0-alpha.0", ">=1.0.0-alpha", True),
 # numeric ordering is numeric, not lexical
 ("1.10.0", ">1.9.0", True), ("1.9.0", ">1.10.0", False), ("10.0.0", "^9.0.0", False),
]
for v, r, want in T:
    got = satisfies(v, r)
    assert got is want, (v, r, want, got)

for bad in ["1.2", "v1.2.3", "01.2.3", "1.2.3.4", "", "1.2.3-", "a.b.c"]:
    try:
        satisfies(bad, "*")
    except ValueError:
        continue
    raise SystemExit("expected ValueError for version %r" % (bad,))
for bad in ["^", "~>", "1.2.3 - ", "foo", ">=abc"]:
    try:
        satisfies("1.0.0", bad)
    except ValueError:
        continue
    raise SystemExit("expected ValueError for range %r" % (bad,))
print("ok")
