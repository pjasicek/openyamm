"""The walkability audit's floor regions on the built map, what borders each one, and where a monster could cross.
usage: regions.py [step]"""
import sys
from collections import Counter, defaultdict
from pathlib import Path
R = Path('/home/pjasicek/github/OpenYAMM')
sys.path.insert(0, str(R / 'level_generation/projects/hesper_stage'))
import check_walkability as w
import numpy as np

step = int(sys.argv[1]) if len(sys.argv) > 1 else 40
w.MONSTER_STEP = step
level = w.load(R / 'level_generation/projects/mm9r_drangheimprison/work/runtime/drangheimprison.blv')
g = w.Graph(level)
sx, sy, sz = level.start
start = g.node_near(sx, sy, sz, tolerance=48)
main = g.region[start]
print('step', step, 'nodes', len(g.z), 'regions', len(g.members), 'start', level.start, 'region size', len(g.members[main]))
region_of_actor = {}
for k, a in enumerate(level.actors):
    n = g.node_near(a['x'], a['y'], a['z'])
    region_of_actor[k] = g.region[n] if n is not None else None
holders = defaultdict(list)
for k, r in region_of_actor.items():
    holders[r].append(k)
for r, acts in sorted(holders.items(), key=lambda kv: -len(kv[1])):
    if r is None:
        print('NO NODE', acts)
        continue
    m = g.members[r]
    c = np.array([w.centre_of(g.cell[n]) for n in m]); z = np.array([g.z[n] for n in m])
    print('region', r, 'MAIN' if r == main else '', 'cells', len(m), 'actors', len(acts), acts[:40],
          'x', int(c[:, 0].min()), int(c[:, 0].max()), 'y', int(c[:, 1].min()), int(c[:, 1].max()), 'z', int(z.min()), int(z.max()))
# Borders between regions: every pair of neighbouring cells of two regions within a drop, wall or open, with a sample.
why = Counter(); samples = {}
for (i, j), ids in g.nodes.items():
    for other in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
        for m in g.nodes.get(other, ()):
            for n in ids:
                a, b = g.region[n], g.region[m]
                if a == b or a > b or len(g.members[a]) < 40 or len(g.members[b]) < 40:
                    continue
                dz = g.z[m] - g.z[n]
                if abs(dz) > 120:
                    continue
                wall = ((i, j) in level.wall_cells or other in level.wall_cells) and level.blocked(
                    *w.centre_of((i, j)), *w.centre_of(other), max(g.z[n], g.z[m]) + w.BODY)
                key = (a, b, 'wall' if wall else 'open', int(round(float(dz) / 10) * 10))
                why[key] += 1
                samples.setdefault(key, (w.centre_of((i, j)), float(g.z[n]), float(g.z[m])))
for key, count in sorted(why.items(), key=lambda kv: (kv[0][:2], -kv[1])):
    if key[2] == 'open' or count > 2:
        print(key, count, samples[key])
