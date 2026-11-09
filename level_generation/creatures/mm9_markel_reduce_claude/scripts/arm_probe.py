#!/usr/bin/env python3
"""Diagnostic for the creature's arm_hand_gate --exact: at one clip frame (48 fps), the arm vertices of one side with the deepest
'inside' reading, the triangle they read against (primitive, centroid, normal) and the true distance to the posed surface.
Usage: arm_probe.py <glb> <clip> <frame48> <side token e.g. ' L '>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
glb, clip, fr, tok = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tris, dom, pid, off = [], [], [], 0
for k in USE:
    tris.append(np.asarray(P[k]['triangles']).reshape(-1, 3) + off); pid += [k] * (len(P[k]['triangles']) // 3 if np.asarray(P[k]['triangles']).ndim == 1 else len(P[k]['triangles']))
    off += len(P[k]['positions']); dom.append(np.array([jn[P[k]['joints'][v][np.argmax(P[k]['weights'][v])]] for v in range(len(P[k]['positions']))]))
tris = np.concatenate(tris).reshape(-1, 3); dom = np.concatenate(dom); pid = np.array(pid)
ARM = 'Clavicle,UpperArm,Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky,Twist'.split(',')
LOW = 'Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky'.split(',')
av = np.array([tok in x and any(a in x for a in ARM) for x in dom]); lv = np.flatnonzero([tok in x and any(a in x for a in LOW) for x in dom])
body_f = np.flatnonzero(~av[tris].any(1))
X = np.concatenate([sp[0] for k, sp in enumerate(m.skinned_positions(m.world(m.sample(clip, fr / 48.0)))) if k in USE])
T = X[tris[body_f]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
pts = X[lv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
q, _ = closest_on_triangles(np.repeat(pts, 40, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
qq = q.reshape(*near.shape, 3)[rows, best]; ff = near[rows, best]
side = np.einsum('ij,ij->i', pts - qq, n[ff]); dep = np.where((side < 0) & (d[rows, best] <= 0.06), -side, 0)
for i in np.argsort(-dep)[:6]:
    f = body_f[ff[i]]
    print(f'vert {lv[i]} {dom[lv[i]]:18s} depth {dep[i]*100:.2f} cm dist {d[i, best[i]]*100:.2f} cm -> face {f} prim {pid[f]} '
          f'centroid {X[tris[f]].mean(0).round(3)} normal {n[ff[i]].round(2)} doms {[dom[v] for v in tris[f]]}')
