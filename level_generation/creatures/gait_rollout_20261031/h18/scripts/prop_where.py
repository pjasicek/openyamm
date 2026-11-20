#!/usr/bin/env python3
"""Per-sample prop (or arm) contacts of contact_probe.py: time, phase, depth and the target bone hit.
    prop_where.py <glb> <clip> <probe: node=prop.glb | armL | armR> [--rate 60]"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402
from contact_probe import vertex_normals, ARM, TARGET  # noqa: E402

body = open_glb(sys.argv[1])
model = glb_pose.Model(body)
names = [n['name'] for n in body.json['nodes']]
clip, probe = sys.argv[2], sys.argv[3]
prim = model.primitives[0]
dominant = [names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
dominant = np.array(dominant)
target = np.array([any(t in d for t in TARGET) and not any(t in d for t in ARM) for d in dominant])
node = None
if '=' in probe:
    node, path = probe.split('=', 1)
    g = glb_pose.Glb(path)
    pts0 = np.concatenate([p['positions'] for p in glb_pose.Model(g).primitives])
else:
    s = probe[-1]
    sel = np.array([d.startswith(f'B_{s}_') and any(t in d for t in ('Forearm', 'Hand', 'Finger')) for d in dominant])
T = model.clip_times(clip)[-1]
for t in np.arange(0, T, 1 / 60):
    W = model.world(model.sample(clip, float(t)))
    points, _ = model.skinned_positions(W)[0]
    normals = vertex_normals(points, prim['triangles'])
    if node:
        M = W[names.index(node)]
        p = pts0 @ M[:3, :3].T + M[:3, 3]
    else:
        p = points[sel]
    tp, tn, td = points[target], normals[target], dominant[target]
    d, i = cKDTree(tp).query(p)
    depth = np.einsum('ij,ij->i', p - tp[i], tn[i])
    inside = (d < 0.04) & (depth < -0.002)
    if inside.any():
        k = np.argmin(np.where(inside, depth, 0))
        print(f't {t:.3f} phase {t / T:.2f} depth {-1000 * depth[k]:.0f} mm  n {inside.sum()}  target {td[i[k]]}  at y {p[k][1]:.2f}')
