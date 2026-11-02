import heapq, os, random, sys
sys.path.insert(0, os.getcwd())
from gridpath import best_path

def raises(f, *a):
    try:
        f(*a)
    except ValueError:
        return True
    return False

def moves(path):
    return "".join({(1, 0): "D", (-1, 0): "U", (0, 1): "R", (0, -1): "L"}[(b[0] - a[0], b[1] - a[1])] for a, b in zip(path, path[1:]))

g = ["....", "....", "...."]
assert best_path(g, (0, 0), (0, 0), 5) == (0, [(0, 0)])
assert best_path(g, (0, 0), (0, 3), 5) == (3, [(0, 0), (0, 1), (0, 2), (0, 3)])
# one turn needed; ties -> D before R at equal cost (both routes have 1 turn)
c, p = best_path(g, (0, 0), (2, 3), 10)
assert c == 5 + 10 and moves(p) == "DDRRR", (c, moves(p))
c, p = best_path(g, (0, 0), (2, 3), 0)
assert c == 5 and moves(p) == "DDRRR"
# walls
assert best_path([".#.", ".#.", "..."], (0, 0), (0, 2), 0) == (6, [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)])
assert best_path(["..#.", "..#."], (0, 0), (0, 3), 0) is None
assert raises(best_path, g, (0, 0), (5, 5), 0) and raises(best_path, ["#."], (0, 0), (0, 1), 0) and raises(best_path, ["#."], (0, 1), (0, 0), 0)
# digit costs
c, p = best_path(["..9.", "...."], (0, 0), (0, 3), 0)
assert c == 5 and moves(p) == "DRRRU"
# turn costs make a straighter, longer route better
grid = ["......", ".####.", "......"]
c, p = best_path(grid, (0, 0), (2, 5), 100)
# one-way arrows
assert best_path([">>>"], (0, 0), (0, 2), 0) == (2, [(0, 0), (0, 1), (0, 2)])
assert best_path([">>>"], (0, 2), (0, 0), 0) is None                     # cannot go against / off an arrow
assert best_path(["<<<"], (0, 0), (0, 2), 0) is None
assert best_path(["..>"], (0, 0), (0, 2), 0) == (2, [(0, 0), (0, 1), (0, 2)])
assert best_path(["..<"], (0, 0), (0, 2), 0) is None                    # entering `<` moving right is illegal
assert best_path(["v.", ".."], (0, 0), (1, 1), 0)[1] == [(0, 0), (1, 0), (1, 1)]   # start arrow forces first move down
assert best_path([">."], (0, 0), (0, 1), 0) == (1, [(0, 0), (0, 1)])
assert best_path(["^."], (0, 0), (0, 1), 0) is None                        # first move must follow the arrow (up leaves the grid)
# must exit an arrow in its direction: >  then wall ahead -> stuck
assert best_path([".>#", "..#"], (0, 0), (1, 1), 0) == (2, [(0, 0), (1, 0), (1, 1)])
assert best_path([".>#", "..."], (0, 0), (1, 2), 0) == (3, [(0, 0), (1, 0), (1, 1), (1, 2)])
# conveyor: goal on arrow ends there
assert best_path([".v.", "..."], (0, 0), (1, 1), 0) == (2, [(0, 0), (1, 0), (1, 1)])
assert best_path([".v.", "..."], (0, 1), (0, 1), 0) == (0, [(0, 1)])
# U-turn is a turn
grid = ["...", "#.#"]
# reversing inside a corridor costs a turn
c, p = best_path(["v"], (0, 0), (0, 0), 3)
assert c == 0

# oracle: Bellman-Ford style relaxation over (cell, dir) keyed by (cost, moves, string); independent of heap order
D = {"D": (1, 0), "L": (0, -1), "R": (0, 1), "U": (-1, 0)}
A = {"^": "U", "v": "D", "<": "L", ">": "R"}
def oracle(grid, s, t, tc):
    R, C = len(grid), len(grid[0])
    if s == t:
        return 0, [s]
    best = {(s, None): (0, 0, "")}
    changed = True
    while changed:
        changed = False
        for (cell, last), key in list(best.items()):
            if cell == t:
                continue
            here = grid[cell[0]][cell[1]]
            for m, (dr, dc) in D.items():
                if here in A and A[here] != m:
                    continue
                nr, nc = cell[0] + dr, cell[1] + dc
                if not (0 <= nr < R and 0 <= nc < C) or grid[nr][nc] == "#":
                    continue
                th = grid[nr][nc]
                if th in A and A[th] != m:
                    continue
                step = int(th) if th.isdigit() else 1
                if last is not None and last != m:
                    step += tc
                nk = (key[0] + step, key[1] + 1, key[2] + m)
                k = ((nr, nc), m)
                if k not in best or nk < best[k]:
                    best[k] = nk
                    changed = True
    cands = [v for (cell, _), v in best.items() if cell == t]
    if not cands:
        return None
    c, n, ms = min(cands)
    path = [s]
    r, cc = s
    for m in ms:
        r += D[m][0]; cc += D[m][1]; path.append((r, cc))
    return c, path

random.seed(4)
for _ in range(400):
    R, C = random.randint(1, 6), random.randint(1, 6)
    cells = ".....123#^v<>"
    grid = ["".join(random.choice(cells) for _ in range(C)) for _ in range(R)]
    free = [(r, c) for r in range(R) for c in range(C) if grid[r][c] != "#"]
    if len(free) < 2:
        continue
    s, t = random.sample(free, 2)
    tc = random.choice([0, 1, 2, 5, 20])
    want = oracle(grid, s, t, tc)
    got = best_path(grid, s, t, tc)
    assert got == want, (grid, s, t, tc, want, got)
print("ok")
