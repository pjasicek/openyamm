#!/usr/bin/env python3
"""Which part a hand is inside (arm_hand_gate's exact depth, split by the part of the nearest face), one clip/frame.
Usage: probe_hand.py <glb> <clip> <time> <side L|R>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
glb, clip, t, side = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
pr = m.primitives[0]; T = np.asarray(pr['triangles']).reshape(-1, 3)
dom = np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))])
rest = np.asarray(pr['positions'], float)
src = np.asarray(Model(Glb(str(HERE / 'before' / 'mm9_nosferatu.glb'))).primitives[0]['positions'], float)
g = np.load(HERE / 'work' / 'glb_parts.npz'); pn = [str(x) for x in g['names']]
sT = np.asarray(Model(Glb(str(HERE / 'before' / 'mm9_nosferatu.glb'))).primitives[0]['triangles']).reshape(-1, 3)
fpart = g['part'][g['mat'] == 0]; vpart_src = -np.ones(len(src), int)
for k in range(len(pn)):
    vpart_src[np.unique(sT[fpart == k])] = k
vpart = vpart_src[cKDTree(src).query(rest)[1]]
tok = f' {side} '
hv = np.array([tok in d and any(k in d for k in ('Hand', 'Finger')) for d in dom])
arm = np.array([tok in d and any(k in d for k in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Twist')) for d in dom])
body_f = np.where(~arm[T].any(1))[0]
X = np.asarray(m.skinned_positions(m.world(m.sample(clip, t)))[0][0])
a, b, c = X[T[body_f, 0]], X[T[body_f, 1]], X[T[body_f, 2]]
n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
pts = X[hv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
q, _ = closest_on_triangles(np.repeat(pts, 40, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(-1, 40); best = d.argmin(1); rows = np.arange(len(pts))
fb = near[rows, best]; side_ = np.einsum('ij,ij->i', pts - q.reshape(-1, 40, 3)[rows, best], n[fb])
dep = np.where((side_ < 0) & (d[rows, best] <= 0.06), -side_, 0)
for k in np.argsort(-dep)[:8]:
    if dep[k] > 0.005:
        f = body_f[fb[k]]; print(f'depth {dep[k]*100:.2f} cm into part {pn[vpart[T[f, 0]]]} (face {f})')
