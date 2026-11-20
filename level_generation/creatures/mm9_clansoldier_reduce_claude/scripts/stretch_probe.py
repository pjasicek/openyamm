#!/usr/bin/env python3
"""Where lod_check.py's stretched faces are: per primitive of a lodcheck GLB, faces whose posed area exceeds 20x the rest area
in the given clip/time (rest area, posed area, centroid, dominant joints). Usage: stretch_probe.py <glb> <clip> <seconds>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['node'] == m.primitives[0]['node']]
rest = m.skinned_positions(m.world({})); pose = m.skinned_positions(m.world(m.sample(sys.argv[2], float(sys.argv[3]))))
area = lambda X, T: np.linalg.norm(np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]]), axis=1) / 2
for k, p in enumerate(P):
    T = np.asarray(p['triangles']).reshape(-1, 3); a0 = area(rest[k][0], T); a1 = area(pose[k][0], T)
    bad = np.where((a1 > 1e-6) & (a1 > 20 * (a0 + 1e-9)))[0]
    for i in bad:
        dom = [jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in T[i]]
        print(k, i, 'rest mm2', round(a0[i] * 1e6, 4), 'posed mm2', round(a1[i] * 1e6, 2), 'at', np.round(rest[k][0][T[i]].mean(0), 3), dom)
