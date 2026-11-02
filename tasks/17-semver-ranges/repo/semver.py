"""npm-style semantic version ranges.

satisfies(version, range_expr) -> bool

`version` is "MAJOR.MINOR.PATCH" with an optional "-prerelease" and optional
"+build" (build metadata is ignored everywhere). A version string that is not
exactly that shape (e.g. "1.2", "v1.2.3", "01.2.3") raises ValueError.

Range grammar (same meaning as npm's `semver`, includePrerelease = false):

* A range is one or more comparator sets joined by `||`; a version satisfies the
  range if it satisfies any set. A set is whitespace-separated terms that must
  ALL hold. An empty set (or `*`) matches any non-prerelease version.
* Plain comparators: `>=1.2.3`, `>1.2.3`, `<=1.2.3`, `<1.2.3`, `=1.2.3`, `1.2.3`.
  Whitespace may separate the operator from the version (`>= 1.2.3`).
* Partial versions and x-ranges: a missing part or `x`, `X`, `*` is a wildcard.
  `1` = `1.x` = `>=1.0.0 <2.0.0`; `1.2` = `1.2.x` = `>=1.2.0 <1.3.0`.
  With operators: `>=1.2` = `>=1.2.0`; `>1.2` = `>=1.3.0`; `<=1.2` = `<1.3.0`;
  `<1.2` = `<1.2.0`; `>1` = `>=2.0.0`; `<=1` = `<2.0.0`; `=1.2` = `1.2.x`.
* Tilde: `~1.2.3` = `>=1.2.3 <1.3.0`; `~1.2` = `>=1.2.0 <1.3.0`;
  `~1` = `>=1.0.0 <2.0.0`; `~1.2.3-beta.2` = `>=1.2.3-beta.2 <1.3.0`.
* Caret (changes that do not modify the left-most non-zero part):
  `^1.2.3` = `>=1.2.3 <2.0.0`; `^0.2.3` = `>=0.2.3 <0.3.0`;
  `^0.0.3` = `>=0.0.3 <0.0.4`; `^1.2.x` = `>=1.2.0 <2.0.0`; `^0.0.x` = `>=0.0.0 <0.1.0`;
  `^0.0` = `>=0.0.0 <0.1.0`; `^1.x` = `>=1.0.0 <2.0.0`; `^0.x` = `>=0.0.0 <1.0.0`;
  `^1.2.3-beta.2` = `>=1.2.3-beta.2 <2.0.0`.
* Hyphen ranges: `1.2.3 - 2.3.4` = `>=1.2.3 <=2.3.4`. A partial lower bound is
  zero-filled (`1.2 - 2.3.4` = `>=1.2.0 <=2.3.4`); a partial upper bound includes
  the whole partial (`1.2.3 - 2.3` = `>=1.2.3 <2.4.0`, `1.2.3 - 2` = `>=1.2.3 <3.0.0`).
* Ordering follows semver 2.0: compare major, minor, patch numerically; a version
  with a prerelease is lower than the same version without; prerelease
  identifiers compare left to right, numeric ones numerically and lower than
  alphanumeric ones, alphanumeric ones in ASCII order, and a shorter list is
  lower when all its identifiers equal the longer one's prefix.
* Prerelease rule: a version that has a prerelease can satisfy a comparator set
  only if at least one comparator in that SAME set has a prerelease and the same
  major.minor.patch tuple as the version. So `1.2.3-beta.4` satisfies
  `^1.2.3-beta.2` but not `^1.2.0`, and `1.2.4-beta.1` does not satisfy
  `^1.2.3-beta.2`.
* An unparseable range raises ValueError.
"""


def satisfies(version, range_expr):
    raise NotImplementedError
