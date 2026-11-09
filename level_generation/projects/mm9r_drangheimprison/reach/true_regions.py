"""The audit's regions with walls tested as polygons: `Level._add_wall` keeps a wall as a plan segment with the face's
whole z range, so a doorway notched into one merged wall polygon counts as solid. Here a move is blocked only when the
polygon itself is at the crossing point and height. usage: true_regions.py [step]"""
import sys
from collections import Counter, defaultdict
from pathlib import Path
R = Path('/home/pjasicek/github/OpenYAMM')
sys.path.insert(0, str(R / 'level_generation/projects/hesper_stage'))
import check_walkability as w
import numpy as np

faces_of_wall = []
original = w.Level._add_wall
def add_wall(self, face):
    before = len(self.walls)
    original(self, face)
    if len(self.walls) > before:
        faces_of_wall.append(face)
w.Level._add_wall = add_wall

def in_polygon(u, v, ring):
    inside = False
    for (u0, v0), (u1, v1) in zip(ring, np.roll(ring, -1, axis=0)):
        if (v0 > v) != (v1 > v) and u < (u1 - u0) * (v - v0) / (v1 - v0) + u0:
            inside = not inside
    return inside

def blocked(self, ax, ay, bx, by, height):
    seen = set()
    for cell in w.cells_along(ax, ay, bx, by):
        for wid in self.wall_cells.get(cell, ()):
            if wid in seen:
                continue
            seen.add(wid)
            x0, y0, x1, y1, z0, z1 = self.walls[wid]
            if not (z0 < height < z1 and w.segments_cross(ax, ay, bx, by, x0, y0, x1, y1)):
                continue
            # the crossing point on the wall's plane, along the wall (u) at this height (v)
            d = np.array([x1 - x0, y1 - y0]); length = np.linalg.norm(d); d = d / length
            m = np.array([bx - ax, by - ay]); n = np.array([-d[1], d[0]])
            t = np.dot(np.array([x0 - ax, y0 - ay]), n) / np.dot(m, n)
            point = np.array([ax, ay]) + m * t
            u = float((point - [x0, y0]) @ d)
            points = faces_of_wall[wid].points
            ring = np.column_stack(((points[:, :2] - [x0, y0]) @ d, points[:, 2]))
            if in_polygon(u, height, ring):
                return True
    return False
w.Level.blocked = blocked

step = int(sys.argv[1]) if len(sys.argv) > 1 else 40
w.MONSTER_STEP = step
level = w.load(R / 'level_generation/projects/mm9r_drangheimprison/work/runtime/drangheimprison.blv')
g = w.Graph(level)
start = g.node_near(*level.start, tolerance=48)
main = g.region[start]
print('step', step, 'regions', len(g.members), 'start region cells', len(g.members[main]))
holders = defaultdict(list)
for k, a in enumerate(level.actors):
    n = g.node_near(a['x'], a['y'], a['z'])
    holders[g.region[n] if n is not None else None].append(k)
for r, acts in sorted(holders.items(), key=lambda kv: -len(kv[1])):
    if r is None:
        print('NO NODE', acts)
        continue
    m = g.members[r]
    c = np.array([w.centre_of(g.cell[n]) for n in m]); z = np.array([g.z[n] for n in m])
    print('region', r, 'MAIN' if r == main else '', 'cells', len(m), 'actors', len(acts), acts,
          'x', int(c[:, 0].min()), int(c[:, 0].max()), 'y', int(c[:, 1].min()), int(c[:, 1].max()), 'z', int(z.min()), int(z.max()))
import pickle
pickle.dump({'region': g.region, 'z': g.z, 'cell': g.cell, 'main': main}, open(f'true_{step}.pkl', 'wb'))

# Directed drops between regions, and what lies between the regions holding actors.
size = {r: len(m) for r, m in g.members.items()}
edges = defaultdict(lambda: [0, None])
for (i, j), ids in g.nodes.items():
    for other in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
        for m in g.nodes.get(other, ()):
            for n in ids:
                a, b = g.region[n], g.region[m]
                dz = g.z[m] - g.z[n]
                if a == b or dz > 0 or dz < -600:
                    continue
                if level.blocked(*w.centre_of((i, j)), *w.centre_of(other), max(g.z[n], g.z[m]) + w.BODY):
                    continue
                key = (a, b)
                e = edges[key]
                e[0] += 1
                if e[1] is None or dz > e[1][2]:
                    e[1] = (w.centre_of((i, j)), float(g.z[n]), float(dz))
holder_regions = [r for r in holders if r is not None]
for a, b in edges:
    pass
for r in holder_regions:
    out = [(b, size[b], e[0], e[1]) for (a, b), e in edges.items() if a == r and size[b] >= 20]
    inc = [(a, size[a], e[0], e[1]) for (a, b), e in edges.items() if b == r and size[a] >= 20]
    print('from', r, 'down to', sorted(out, key=lambda t: -t[1])[:12])
    print('into', r, 'from above', sorted(inc, key=lambda t: -t[1])[:12])

# The ladders' ends, and the border of each region that holds actors other than the start's.
import json
scene = json.load(open(R / 'level_generation/projects/mm9r_drangheimprison/work/runtime/drangheimprison.scene.yml'))
def region_at(x, y, z, tol=120):
    best = None
    for dx in range(-96, 97, 16):
        for dy in range(-96, 97, 16):
            for n in g.nodes.get(w.cell_of(x + dx, y + dy), ()):
                if abs(g.z[n] - z) <= tol and (best is None or dx * dx + dy * dy < best[0]):
                    best = (dx * dx + dy * dy, g.region[n], float(g.z[n]))
    return best and (best[1], size[best[1]], best[2])
for l in scene['ladders']:
    print('ladder', {k: v for k, v in l.items() if k in ('name', 'id', 'x', 'y', 'z', 'bottom', 'top', 'position', 'base', 'top_exit', 'foot', 'exit')})
    print('   ', str(l)[:300])
r = [x for x in holders if x is not None and len(holders[x]) == 6][0]
pairs = Counter()
sample = {}
for n in g.members[r]:
    i, j = g.cell[n]
    for other in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
        for m in g.nodes.get(other, ()):
            if g.region[m] != r:
                key = (g.region[m], size[g.region[m]], round(float(g.z[m] - g.z[n]) / 10) * 10)
                pairs[key] += 1
                sample.setdefault(key, (w.centre_of((i, j)), float(g.z[n])))
for key, c in pairs.most_common(30):
    print('hatchlings border', key, c, sample[key])
