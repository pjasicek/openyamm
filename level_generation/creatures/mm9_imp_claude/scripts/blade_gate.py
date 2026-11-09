#!/usr/bin/env python3
"""Trident against the body: every clip at 48 fps, points along the shaft and blades (densified) against the skin, excluding
the holding hand and fingers. Signed distance to the nearest triangle by its face normal; a point behind a face within 6 cm
is inside. Usage: blade_gate.py <full glb> <out json>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, '../claude_shared')
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
g = Glb(Path(sys.argv[1])); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]
jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['node'] == m.primitives[0]['node'] and p['skinned']]
tri, off, dom = [], 0, []
for p in P:
    tri.append(p['triangles'] + off); off += len(p['positions'])
    dom.append(np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]))
tri = np.concatenate(tri); dom = np.concatenate(dom)
item = dom == 'Yweaponbase'
hand = np.array([(' R Hand' in d or ' R Finger' in d or 'Xwrap' in d or 'Xtongue' in d) for d in dom])
body_f = np.where(~(item[tri].any(1) | hand[tri].any(1)))[0]
itf = np.where(item[tri].all(1))[0]
USE = [k for k, pr in enumerate(m.primitives) if pr['node'] == m.primitives[0]['node'] and pr['skinned']]
BARY = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1 / 3, 1 / 3, 1 / 3]])
iv = np.where(item)[0]
ax = np.linalg.svd(np.concatenate([p['positions'] for p in P])[iv] - np.concatenate([p['positions'] for p in P])[iv].mean(0))[2][0]
tt = np.concatenate([p['positions'] for p in P])[iv] @ ax
E0, E1 = iv[tt.argmin()], iv[tt.argmax()]
out = {}
for clip in m.clips:
    dur = max(m.clip_times(clip))
    worst = (0.0, 0, None); bad = 0
    for k, t in enumerate(np.arange(0, dur + 1e-6, 1 / 48)):
        sp = m.skinned_positions(m.world(m.sample(clip, float(t))))
        X = np.concatenate([sp[i][0] for i in USE])
        pts = np.einsum('kb,fbc->fkc', BARY, X[tri[itf]]).reshape(-1, 3)
        ends = X[[E0, E1]]                     # the long shaft faces have no interior points: a line of 240 samples
        pts = np.vstack([pts, ends[0] + np.outer(np.linspace(0, 1, 240), ends[1] - ends[0])])
        T = X[tri[body_f]]
        a, b, c = T[:, 0], T[:, 1], T[:, 2]
        n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        tree = cKDTree((a + b + c) / 3)
        d0, near = tree.query(pts, k=16)
        q, _ = closest_on_triangles(np.repeat(pts, 16, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
        d = np.linalg.norm(np.repeat(pts, 16, 0) - q, axis=1).reshape(near.shape)
        best = d.argmin(1); rows = np.arange(len(pts))
        side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
        dep = np.where((side < 0) & (d[rows, best] <= 0.06), d[rows, best], 0.0)
        if dep.max() > worst[0]:
            worst = (float(dep.max()), k, dom[tri[body_f][near[rows, best][dep.argmax()], 0]])
        bad += int(dep.max() > 0.01)
    out[clip] = {'worst_cm': round(worst[0] * 100, 1), 'frame48': worst[1], 'bone': worst[2], 'frames_over_1cm': bad}
    print(clip, out[clip])
json.dump(out, open(sys.argv[2], 'w'), indent=1)
