"""Cheapest path on a grid with turn costs and one-way tiles.

best_path(grid, start, goal, turn_cost) -> (cost, path) or None

* `grid` is a list of equal-length strings. Cells: `.` open (cost 1 to enter), a digit `1`-`9`
  (cost = that digit to enter), `#` wall (never enterable), and the one-way arrows `^ v < >`
  (cost 1 to enter, see below).
* `start` and `goal` are (row, col) tuples; both must be inside the grid and not walls, else
  ValueError. Entering the start cell is free (it is never "entered"). `turn_cost` is an int >= 0.
* A move goes to one of the 4 orthogonal neighbours, costs the neighbour's entry cost, and
  adds `turn_cost` if the move direction differs from the PREVIOUS move's direction (the first
  move never pays a turn cost). A U-turn (reversing) counts as a turn.
* One-way tiles: an arrow cell can only be ENTERED by a move in the arrow's direction, and
  once you stand on it your NEXT move must be in that same direction (so `>` is entered
  moving right and left moving right). Standing on an arrow cell that is the goal ends the
  path there, so the "next move" rule does not apply to a goal cell. The start cell may be an
  arrow cell: its first move must then follow the arrow.
* Return `(total_cost, path)` where `path` is the list of (row, col) cells from start to goal
  inclusive; start == goal gives `(0, [start])`. If the goal cannot be reached return None.
* Tie-breaks (the answer is unique): among minimum-cost paths prefer the one with FEWER
  moves; among those prefer the lexicographically smallest move string, where each move is
  one of `D` (row+1), `L` (col-1), `R` (col+1), `U` (row-1) and the letters compare in plain
  alphabetical order (D < L < R < U).
* Paths may revisit cells if that is genuinely cheapest (turn costs can make that so).
"""


def best_path(grid, start, goal, turn_cost):
    raise NotImplementedError
