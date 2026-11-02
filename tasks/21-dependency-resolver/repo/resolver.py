"""A small dependency resolver.

resolve(requirements, index) -> dict[str, str]

* `index[pkg][version]` is a dict of that release's dependencies: `{dep_name: constraint}`.
  Versions are dotted non-negative integers ("1", "1.2", "1.10.3"); compare them numerically
  component by component, a missing component counting as 0 ("1.0" == "1" == "1.0.0").
  When two keys of one package compare equal, the one listed first in `index[pkg]` is preferred.
* A constraint is "*" (anything) or one or more space-separated comparators joined as AND:
  `>=1.2`, `>1`, `<=2.0`, `<3`, `==1.4`, `!=1.3` (e.g. ">=1.2 <3 !=2.1").
* `requirements` is `{pkg: constraint}` for the root. Return `{pkg: chosen_version}` for every
  package that ends up needed (roots plus the transitive dependencies of the CHOSEN versions),
  such that every chosen version satisfies every constraint placed on that package by the
  roots and by the chosen versions of other packages. Dependency cycles are allowed.
* Choice rule (this makes the answer unique): repeatedly take the alphabetically smallest
  needed package that has no version yet, and try its candidate versions from the highest to
  the lowest, keeping the first choice that can be completed; if the rest cannot be completed,
  backtrack and try the next lower version. So the result is the first complete solution in
  that depth-first order.
* A package not in `index` has no versions, so it cannot be satisfied. If no solution exists,
  raise ResolutionError. Version strings in the result are exactly the keys used in `index`.
* Must handle a few dozen packages with a few versions each in well under a second when
  there is no conflict, and must not recurse unboundedly on cycles.
"""


class ResolutionError(Exception):
    pass


def resolve(requirements, index):
    raise NotImplementedError
