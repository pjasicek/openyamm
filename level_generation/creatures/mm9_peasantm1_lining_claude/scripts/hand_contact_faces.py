#!/usr/bin/env python3
"""Which faces the creature's arm_hand_gate.py (--outer-only --exact) reads a hand as inside of, for one clip/frame/side: the
nearest outer body face per hand vertex deeper than 1 cm, reported as original or new (lining) triangles of each primitive,
with the lining op (line.py vtags of its vertices). Same face sets as the gate (every face not on that arm, outer_surface).
Usage: hand_contact_faces.py <glb> <lining npz> <clip> <frame48> <side token e.g. ' L '>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
C = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(C / 'claude_shared' / 'floor')); sys.path.insert(0, str(C / 'claude_shared'))
sys.path.insert(0, str(C / 'mm9_guard_claude' / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
from outer_surface import outer_faces  # noqa: E402
glb, linz, clip, f48, tok = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
g = Glb(Path(glb)); m = Model(g); z = np.load(linz)
names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
doc = g.json; nd = next(n for n in doc['nodes'] if n.get('name') == 'PeasantM1' and 'mesh' in n)
pn = [doc['materials'][p['material']]['name'] for p in doc['meshes'][nd['mesh']]['primitives']]
tri_all, off, dom, owner = [], 0, [], []
for k in USE:
    pr = P[k]; T = pr['triangles']; n0 = int(z[f'nvert_{pn[k]}'])
    tri_all.append(T + off); off += len(pr['positions'])
    dom += [jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]
    tags = z[f'vtag_{pn[k]}']
    for t in T:
        new = [v for v in t if v >= n0]
        owner.append((pn[k], tags[new[0] - n0].split('|')[0] if new else 'orig'))
tris = np.concatenate(tri_all); dom = np.array(dom)
hand = ['Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
arm = ['Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Twist']
hv = np.where(np.array([tok in d and any(k in d for k in (['Forearm'] if __import__('os').environ.get('FOREARM') else hand)) for d in dom]))[0]
av = np.array([tok in d and any(k in d for k in arm) for d in dom])
body_f = np.where(~av[tris].any(1))[0]
rest = np.concatenate([m.skinned_positions(m.world({}))[k][0] for k in USE])
body_f = body_f[outer_faces(rest, tris, body_f)]
X = np.concatenate([m.skinned_positions(m.world(m.sample(clip, f48 / 48.0)))[k][0] for k in USE])
T = X[tris[body_f]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
pts = X[hv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
q, _ = closest_on_triangles(np.repeat(pts, 40, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
dep = np.where((side < 0) & (d[rows, best] <= 0.06), -side, 0.0)
from collections import Counter
cnt = Counter(); mx = {}
for i in np.where(dep > 0.01)[0]:
    f = body_f[near[i, best[i]]]; key = owner[f]; cnt[key] += 1; mx[key] = max(mx.get(key, 0), dep[i])
print(clip, f48, repr(tok), 'hand verts >1 cm:', int((dep > 0.01).sum()), 'max', round(float(dep.max()) * 100, 1), 'cm')
for k, v in cnt.most_common():
    print('  ', k, v, 'verts, max', round(mx[k] * 100, 1), 'cm')
