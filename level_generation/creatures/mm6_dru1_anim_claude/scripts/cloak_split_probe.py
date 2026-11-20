"""Probe how the cloak joins the torso inside Smart Topology piece P00 (work/st_v1_parts.blend).
Flood-fills P00 from its hem vertices through mesh edges, limited to z < ZC, for several ZC, and reports how far the
fill reaches (does it leak onto the chest front / arms below the shoulder?). Args: -- <parts blend>"""
import bpy, bmesh, sys
import numpy as np
from collections import deque
src = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects['P00']
me = ob.data
co = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices])
nbr = [[] for _ in co]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
seed = [i for i in range(len(co)) if co[i, 2] < 0.2]
print('PROBE verts', len(co), 'seed', len(seed))
for zc in (1.40, 1.42, 1.44, 1.46, 1.48):
    seen = set(seed); q = deque(seed)
    while q:
        i = q.popleft()
        for j in nbr[i]:
            if j not in seen and co[j, 2] < zc:
                seen.add(j); q.append(j)
    s = np.array(sorted(seen))
    rest = np.setdiff1d(np.arange(len(co)), s)
    chest = [(i) for i in s if co[i, 2] > 0.95 and co[i, 2] < 1.3 and abs(co[i, 0]) < 0.12 and co[i, 1] < -0.08]
    print('PROBE zc', zc, 'reached', len(s), 'rest', len(rest), 'chest-front reached', len(chest),
          'rest z range', (round(float(co[rest, 2].min()), 3), round(float(co[rest, 2].max()), 3)) if len(rest) else None)
