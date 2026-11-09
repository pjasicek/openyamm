#!/usr/bin/env python3
"""Which forearm vertex is inside which body face (arm_hand_gate.py --outer-only --exact 'forearm' metric) at one clip frame.
Usage: probe_forearm.py <glb> <clip> <frame48> <L|R>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
sys.path.insert(0, str(HERE.parent / 'mm9_wyrde_claude' / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
from outer_surface import outer_faces  # noqa: E402
glb, clip, fr, side = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
model = Model(Glb(glb)); names = [n.get('name') for n in model.glb.json['nodes']]; jn = [names[j] for j in model.joints]
P = model.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
S = Model(Glb(str(HERE / 'before' / 'mm9_wyrde.glb'))); g = np.load(HERE / 'work' / 'glb_parts.npz')
tri_all, off, dom, vpart = [], 0, [], []
for k in USE:
    pr = P[k]; tri_all.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
    src = S.primitives[k]; vp = np.full(len(src['positions']), -1); vp[src['triangles'].ravel()] = np.repeat(g['part'][g['mat'] == k], 3)
    _, j = cKDTree(src['positions']).query(pr['positions']); vpart.append(vp[j])
tris = np.concatenate(tri_all); dom = np.concatenate(dom); vpart = np.concatenate(vpart)
tok = f' {side} '
arm = [j for j in jn if tok in j and any(k in j for k in 'Clavicle,UpperArm,Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky,Twist'.split(','))]
fv = np.flatnonzero(np.isin(dom, [j for j in jn if tok in j and 'Forearm' in j]))
av = np.isin(dom, arm); body_f = np.flatnonzero(~av[tris].any(1))
rest = np.concatenate([model.skinned_positions(model.world({}))[k][0] for k in USE])
body_f = body_f[outer_faces(rest, tris, body_f)]
X = np.concatenate([model.skinned_positions(model.world(model.sample(clip, fr / 48.0)))[k][0] for k in USE])
T = X[tris[body_f]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
pts = X[fv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
q, _ = closest_on_triangles(np.repeat(pts, 40, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
side_ = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
dep = np.where((side_ < 0) & (d[rows, best] <= 0.06), -side_, 0.0)
for i in np.argsort(-dep)[:8]:
    f = body_f[near[i, best[i]]]
    print(f'forearm v {fv[i]} part {vpart[fv[i]]} dom {dom[fv[i]]} depth {dep[i] * 100:.2f} cm  <- face {f} part {vpart[tris[f, 0]]} dom {dom[tris[f, 0]]} rest {rest[fv[i]].round(3)}')
