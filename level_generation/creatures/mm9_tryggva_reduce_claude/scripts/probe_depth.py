#!/usr/bin/env python3
"""Which surface does an arm point sink into? (arm_hand_gate regressions on a candidate.) For <clip> at 48 fps frame <f>,
the side's hand (or forearm) vertices' signed depth behind the nearest non-arm face (the gate's exact_depth rule, without
the outer-surface filter); prints the 12 deepest points with the target face's part code (glb_parts.npz) and its
installed face index (candidate faces matched to installed faces by corner positions).
Usage: probe_depth.py <glb> <clip> <frame48> <L|R> [hand|forearm]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
import glbio, cfg  # noqa: E402
glb, clip, f48, side = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]; what = sys.argv[5] if len(sys.argv) > 5 else 'hand'
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tris, dom, off, mat = [], [], 0, []
for k in USE:
    pr = P[k]; tris.append(pr['triangles'] + off); off += len(pr['positions']); mat += [k] * len(pr['triangles'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tris); dom = np.concatenate(dom); mat = np.array(mat)
tok = f' {side} '
keys = ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky') if what == 'hand' else ('Forearm',)
arm = ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Twist')
pv = np.flatnonzero([tok in d and any(k in d for k in keys) for d in dom])
av = np.array([tok in d and any(k in d for k in arm) for d in dom]); body = np.flatnonzero(~av[tris].any(1))
rest = np.concatenate([m.skinned_positions(m.world({}))[k][0] for k in USE])
X = np.concatenate([m.skinned_positions(m.world(m.sample(clip, f48 / 48.0)))[k][0] for k in USE])
T = X[tris[body]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
pts = X[pv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
q, _ = closest_on_triangles(np.repeat(pts, 40, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
sd = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
dep = np.where((sd < 0) & (d[rows, best] <= 0.06), -sd, 0.0)
# installed part of the target face: match its rest centroid to glb_parts centroids
g = np.load(HERE / 'work' / 'glb_parts.npz'); gk = cKDTree(g['cen'])
for i in np.argsort(-dep)[:12]:
    f = body[near[i, best[i]]]; cen = rest[tris[f]].mean(0); dd, gi = gk.query(cen)
    print(f'depth {dep[i] * 100:.2f} cm  point {dom[pv[i]]:18s} -> face {f} prim {mat[f]} dom {dom[tris[f][0]]:16s} part {g["part"][gi]} (match {dd * 1000:.1f} mm)')
