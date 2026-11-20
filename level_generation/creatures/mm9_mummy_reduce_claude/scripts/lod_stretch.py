#!/usr/bin/env python3
"""Faces of one LOD mesh that stretch over 20x their rest area in a clip (30 Hz), with their dominant bones (glb_pose skips meshes
named LOD1-3, so the LOD mesh is renamed in memory). Usage: lod_stretch.py <glb> <lod 1-3> <clip,...>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, lod, clips = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(',')
g = Glb(glb); doc = g.json
node = next(n for n in doc['nodes'] if n.get('name') == 'Mummy')
node['mesh'] = doc['meshes'][node['mesh']]['extras']['openyamm_lods'][lod - 1]; doc['meshes'][node['mesh']]['name'] = 'probe'
m = Model(g); names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
area = lambda P, T: np.linalg.norm(np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]), axis=1) / 2
rest = [area(p['positions'], p['triangles']) for p in m.primitives]
for clip in clips:
    worst = {}
    for t in np.arange(0, m.clip_times(clip)[-1] + 1e-6, 1 / 30):
        for k, (P, _) in enumerate(m.skinned_positions(m.world(m.sample(clip, float(t))))):
            T = m.primitives[k]['triangles']; a = area(P, T); r = a / (rest[k] + 1e-9)
            for f in np.flatnonzero((a > 1e-6) & (r > 20)):
                if r[f] > worst.get((k, f), (0,))[0]: worst[(k, f)] = (r[f], t, a[f])
    for (k, f), (r, t, a) in worst.items():
        p = m.primitives[k]; v = p['triangles'][f]
        bones = {names[p['joints'][i][p['weights'][i].argmax()]] for i in v}
        print(clip, 'prim', k, 'face', f, f'x{r:.0f} at {t:.2f}s area {a * 1e4:.2f} cm2 rest {rest[k][f] * 1e4:.4f} cm2', bones)
