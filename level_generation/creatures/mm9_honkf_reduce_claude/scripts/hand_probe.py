#!/usr/bin/env python3
"""Where a hand is 'inside' in arm_hand_gate.py --outer-only --exact (same method): worst hand vertices of one side at one clip
time, with the nearest outer body face's primitive, rest centroid and depth. Usage: hand_probe.py <glb> <clip> <t> <L|R>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
C = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(C / 'claude_shared' / 'floor')); sys.path.insert(0, str(C / 'claude_shared')); sys.path.insert(0, str(C / 'mm9_zombie_claude' / 'scripts'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
from outer_surface import outer_faces
glb, clip, t, side = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives[:3]; tris, dom, pid, off = [], [], [], 0
for k, pr in enumerate(P):
    tris.append(np.asarray(pr['triangles']) + off); off += len(pr['positions']); pid += [k] * len(pr['triangles'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tris); dom = np.concatenate(dom); pid = np.array(pid)
tok = f' {side} '
hv = np.where(np.array([tok in j and any(k in j for k in ('Hand', 'Finger', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb')) for j in dom]))[0]
av = np.array([tok in j and any(k in j for k in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb')) for j in dom])
body_f = np.where(~av[tris].any(1))[0]
rest = np.concatenate([np.asarray(s[0]) for s in m.skinned_positions(m.world({}))[:3]])
body_f = body_f[outer_faces(rest, tris, body_f)]
X = np.concatenate([np.asarray(s[0]) for s in m.skinned_positions(m.world(m.sample(clip, t)))[:3]])
T = X[tris[body_f]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
pts = X[hv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
q, _ = closest_on_triangles(np.repeat(pts, 40, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
fb = near[rows, best]; side_ = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[fb])
dep = np.where((side_ < 0) & (d[rows, best] <= 0.06), -side_, 0.0)
for i in np.argsort(-dep)[:6]:
    f = body_f[fb[i]]
    print(f'depth {dep[i] * 100:.2f} cm hand vertex {hv[i]} ({dom[hv[i]]}) rest {rest[hv[i]].round(3)} -> face {f} prim {pid[f]} rest centroid {rest[tris[f]].mean(0).round(3)} dom {dom[tris[f][0]]}')
