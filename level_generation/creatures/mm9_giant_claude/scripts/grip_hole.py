#!/usr/bin/env python3
"""The right fist's free hole round MM9's handle axis, on the skinned mesh (glb_pose), at a clip time where MM9's curl holds the
mallet. In the plane across the axis: candidate centres on a grid; a centre counts when it lies outside the skin (nearest face
normal), the hand's vertices in a slab along the axis surround it (largest angular gap < GAP deg), and its clearance is the distance
to the nearest hand vertex. Reports the best centre in the hand's frame, its clearance, and where MM9's axis runs.
Args: <glb> <clip> <time> [out json]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
GAP = 100
m = Model(Glb(sys.argv[1])); clip, t = sys.argv[2], float(sys.argv[3])
doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; jn = [names[j] for j in m.joints]
w = m.world(m.sample(clip, t))
sk = m.skinned_positions(w)
PR = m.primitives
P = np.vstack([x[0] for x in sk]); off = np.cumsum([0] + [len(x[0]) for x in sk])
T = np.vstack([np.asarray(x[1]).reshape(-1, 3) + o for x, o in zip(sk, off)])
J = np.vstack([p['joints'] for p in PR]); W = np.vstack([p['weights'] for p in PR])
dom = np.array([jn[J[i, np.argmax(W[i])]] for i in range(len(J))])
hand = np.array([(' R ' in d) and any(k in d for k in ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for d in dom])
X = w[names.index('Xhammer')]; AX = X[:3, 1] / np.linalg.norm(X[:3, 1]); O = X[:3, 3]
H = w[names.index('Bip01 R Hand')]
hc = P[hand].mean(0)
A0 = O + AX * ((hc - O) @ AX)                         # MM9's axis point nearest the hand's centre
e1 = np.cross(AX, [0, 1, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(AX, e1)
fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
fc = P[T].mean(1); kf = cKDTree(fc)
HP = P[hand]; kh = cKDTree(HP)
best = None
for a in np.arange(-0.12, 0.121, 0.004):
    for b in np.arange(-0.12, 0.121, 0.004):
        G = A0 + e1 * a + e2 * b
        d, i = kh.query(G)
        _, k = kf.query(G)
        if (G - fc[k]) @ fn[k] < 0: continue          # inside the skin
        q = HP - G; al = q @ AX; sl = np.abs(al) < 0.04; q = q[sl] - np.outer(al[sl], AX)
        r = np.linalg.norm(q, axis=1); near = r < 0.11
        if near.sum() < 10: continue
        ang = np.sort(np.arctan2(q[near] @ e2, q[near] @ e1))
        gap = np.degrees(np.max(np.diff(np.r_[ang, ang[0] + 2 * np.pi])))
        if gap > GAP: continue
        if best is None or d > best[0]: best = (d, G, gap)
d, G, gap = best
Hi = np.linalg.inv(H)
res = {'clip': clip, 'time': t, 'clear_cm': round(float(d) * 100, 2), 'gap_deg': round(float(gap), 1),
       'G_hand': (Hi @ np.r_[G, 1])[:3].tolist(), 'axis_hand': (Hi[:3, :3] @ AX).tolist(),
       'mm9_axis_offset_cm': round(float(np.linalg.norm((G - A0) - AX * ((G - A0) @ AX))) * 100, 2)}
print('HOLE', json.dumps(res))
if len(sys.argv) > 4: json.dump(res, open(sys.argv[4], 'w'), indent=1)
