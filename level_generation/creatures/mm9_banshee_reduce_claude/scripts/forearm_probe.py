#!/usr/bin/env python3
"""Which primitive the arm gate's forearm depth comes from: forearm vertices (dominant joint '<side> Forearm' in the
gate alias GLB) against each other primitive, depth behind the nearest triangle (<= 6 cm), at one clip time.
Usage: forearm_probe.py <alias glb> <clip> <frame48> <side token e.g. ' L '>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
glb, clip, fr, tok = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
m = Model(Glb(glb)); doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in m.joints]
mats = [doc['materials'][p['material']]['name'] for p in doc['meshes'][0]['primitives']]
posed = m.skinned_positions(m.world(m.sample(clip, fr / 48)))
fa = [i for i, n in enumerate(names) if tok in n and n.endswith('Forearm')]
for pi, ((X, T), pr) in enumerate(zip(posed, m.primitives)):
    dom = pr['joints'][np.arange(len(pr['joints'])), pr['weights'].argmax(1)]
    fv = np.isin(dom, fa)
    if fv.sum() == 0:
        continue
    pts = X[fv]
    for pj, (Y, U) in enumerate(posed):
        if pj == pi:
            continue
        a, b, c = Y[U[:, 0]], Y[U[:, 1]], Y[U[:, 2]]
        n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        _, near = cKDTree((a + b + c) / 3).query(pts, k=min(40, len(U))); near = near.reshape(len(pts), -1)
        q, _ = closest_on_triangles(np.repeat(pts, near.shape[1], 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
        d = np.linalg.norm(np.repeat(pts, near.shape[1], 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
        side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
        dep = np.where((side < 0) & (d[rows, best] <= 0.06), -side, 0.0)
        if dep.max() > 0.005:
            print(f'{mats[pi]} forearm vs {mats[pj]}: max {dep.max() * 100:.1f} cm, verts > 1 cm {(dep > 0.01).sum()}')
