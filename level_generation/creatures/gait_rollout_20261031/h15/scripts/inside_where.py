#!/usr/bin/env python3
"""Where the contact probe finds arm or prop points inside the legs/trunk: per clip sample, the deepest points with
their dominant bone and the target bone they are under (diagnosis of the probe's findings).

    inside_where.py <glb> <clip> <time> [node=attachment.glb]
"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402
from contact_probe import vertex_normals, ARM, TARGET  # noqa: E402

glb = open_glb(sys.argv[1])
model = glb_pose.Model(glb)
names = [n['name'] for n in glb.json['nodes']]
prim = model.primitives[0]
dom = [names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
arm = np.array([any(t in d for t in ('Forearm', 'Hand', 'Finger')) for d in dom])
target = np.array([any(t in d for t in TARGET) and not any(t in d for t in ARM) for d in dom])
W = model.world(model.sample(sys.argv[2], float(sys.argv[3])))
points, _ = model.skinned_positions(W)[0]
normals = vertex_normals(points, prim['triangles'])
tree = cKDTree(points[target])
tidx = np.where(target)[0]
probes = {'arms': (points[arm], np.where(arm)[0])}
for item in sys.argv[4:]:
    node, path = item.split('=', 1)
    pts = np.concatenate([p['positions'] for p in glb_pose.Model(glb_pose.Glb(path)).primitives])
    M = W[names.index(node)]
    probes[node] = (pts @ M[:3, :3].T + M[:3, 3], None)
for name, (p, ids) in probes.items():
    d, i = tree.query(p)
    depth = np.einsum('ij,ij->i', p - points[tidx[i]], normals[tidx[i]])
    inside = np.where((d < 0.04) & (depth < -0.002))[0]
    print(name, len(inside), 'inside')
    for k in inside[np.argsort(depth[inside])][:8]:
        own = dom[ids[k]] if ids is not None else name
        print(f'  {own:18} under {dom[tidx[i[k]]]:12} depth {1000 * depth[k]:.0f} mm at {np.round(p[k], 3)}')
