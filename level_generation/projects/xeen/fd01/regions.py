"""Connected regions of maze 52 under different gate states (passable: 0, 2, 4, door 9)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
R = _REPO_ROOT + '/reference/mm4_5_world_of_xeen/unpacked/'
d = json.load(open(R + 'maps/dark_initial_state/maze0052.dat.json'))
W = [[list(c['wallsNESW']) for c in row] for row in d['cells']]
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
def alter(x, y, dr, v):
    W[y][x][dr] = v
def ok(v):
    return v in (0, 2, 4, 9)
def regions():
    seen = {}
    rid = 0
    for y in range(16):
        for x in range(16):
            if (x, y) in seen:
                continue
            if all(not ok(v) for v in W[y][x]):
                continue
            stack = [(x, y)]
            seen[(x, y)] = rid
            while stack:
                cx, cy = stack.pop()
                for dr, (dx, dy) in enumerate(DIRS):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < 16 and 0 <= ny < 16 and ok(W[cy][cx][dr]) and (nx, ny) not in seen:
                        seen[(nx, ny)] = rid
                        stack.append((nx, ny))
            rid += 1
    out = {}
    for k, v in seen.items():
        out.setdefault(v, []).append(k)
    return out
def show(tag):
    print('==', tag)
    for k, cells in regions().items():
        if len(cells) > 0:
            print(k, len(cells), sorted(cells, key=lambda c: (c[1], c[0])))
show('initial')
# levers (6,5) and (8,5)
for a in [(4, 5, 0, 0), (4, 5, 2, 0), (4, 4, 0, 0), (4, 6, 2, 0)]:
    alter(*a)
show('lever 6,5')
for a in [(10, 5, 2, 0), (10, 4, 0, 0), (11, 5, 3, 0), (10, 5, 1, 0)]:
    alter(*a)
show('lever 8,5')
for a in [(13, 7, 0, 0), (13, 7, 2, 0), (13, 6, 0, 0), (13, 8, 2, 0)]:
    alter(*a)
show('silver skull')
for a in [(13, 11, 0, 0), (13, 11, 2, 0), (13, 10, 0, 0), (13, 12, 2, 0)]:
    alter(*a)
show('gold skull')
