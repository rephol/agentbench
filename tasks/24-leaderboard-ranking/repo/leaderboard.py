"""Leaderboard.

Ordering: higher score first; equal scores are ordered by name ascending (plain string
comparison, case-sensitive). Ranks use STANDARD COMPETITION ranking: players with equal
scores share a rank and the next rank skips (scores 90, 80, 80, 70 -> ranks 1, 2, 2, 4).

API (names are strings; scores are int or float; a NaN score raises ValueError; bool scores
raise TypeError):

* set_score(name, score): add the player or replace their score.
* remove(name): remove a player; KeyError if unknown.
* rank(name) -> int; KeyError if unknown.
* top(n) -> list of (rank, name, score) for the first n players in order (n <= 0 gives []).
* page(number, size) -> list of (rank, name, score); pages are 1-based over the same ordering;
  an out-of-range page is []. number < 1 or size < 1 raises ValueError.
* around(name, k) -> list of (rank, name, score): the player plus up to k players before and
  up to k after in the ordering, clamped at both ends (k < 0 raises ValueError); KeyError if unknown.
* percentile(name) -> float: 100 * (number of OTHER players with a strictly lower score) /
  (number of other players). With a single player it is 100.0. KeyError if unknown.
* len(board) is the number of players.
"""
from pagination import slice_window, paginate


class Board:
    def __init__(self):
        self._scores = {}

    def __len__(self):
        return len(self._scores)

    def set_score(self, name, score):
        self._scores[name] = score

    def remove(self, name):
        del self._scores[name]

    def _ordered(self):
        return sorted(self._scores.items(), key=lambda kv: -kv[1])

    def _ranked(self):
        out = []
        for i, (name, score) in enumerate(self._ordered()):
            out.append((i + 1, name, score))
        return out

    def rank(self, name):
        for r, n, _ in self._ranked():
            if n == name:
                return r
        raise KeyError(name)

    def top(self, n):
        return self._ranked()[:n]

    def page(self, number, size):
        return paginate(self._ranked(), number, size)

    def around(self, name, k):
        rows = self._ranked()
        idx = [n for _, n, _ in rows].index(name)
        return slice_window(rows, idx, k)

    def percentile(self, name):
        s = self._scores[name]
        lower = sum(1 for v in self._scores.values() if v <= s)
        return 100.0 * lower / len(self._scores)
