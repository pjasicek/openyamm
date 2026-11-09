#!/usr/bin/env python3
"""Lowest posed vertex of one LOD mesh over a clip (glb_pose skips meshes named LOD1-3, so the LOD mesh is renamed in memory).
Usage: lod_low.py <glb> <lod 1-3> <clip>"""
import json, re, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose
from glb_pose import Glb, Model
glb, lod, clip = sys.argv[1], int(sys.argv[2]), sys.argv[3]
g = Glb(glb); doc = g.json
node = next(n for n in doc['nodes'] if n.get('name') == 'Mummy')
node['mesh'] = doc['meshes'][node['mesh']]['extras']['openyamm_lods'][lod - 1]; doc['meshes'][node['mesh']]['name'] = 'probe'
m = Model(g); names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
best = (9, None)
for t in np.arange(0, m.clip_times(clip)[-1] + 1e-6, 1 / 30):
    for k, (P, _) in enumerate(m.skinned_positions(m.world(m.sample(clip, float(t))))):
        i = P[:, 1].argmin()
        if P[i, 1] < best[0]: best = (P[i, 1], (round(float(t), 3), k, int(i)))
v, (t, k, i) = best; p = m.primitives[k]
print('LOD', lod, clip, 'lowest', round(v * 100, 2), 'cm at', t, 'prim', k, 'rest', p['positions'][i].round(3),
      [(names[j], round(float(w), 2)) for j, w in zip(p['joints'][i], p['weights'][i]) if w > 0])
