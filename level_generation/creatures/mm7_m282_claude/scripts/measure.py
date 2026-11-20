#!/usr/bin/env python3
"""Mesh measurements for the Medusa rig (python3, numpy/scipy) from work/step1_mesh.npz (step1_clean.py).
- Axial centreline: geodesic distance over the skin piece from the rattle tip; the centroid of each 4 cm level-set band
  gives the tail/column centreline up to the hips (the bands stay single rings until the arms branch off).
- Arms: geodesic distance from each wrist (the skin vertices next to the hand piece); level-set band centroids give the
  arm axis from the wrist to the armpit.
Prints the tables; writes work/measure.json (axial [x,y,z,r] by arc, arm polylines)."""
import json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[1]
d = np.load(P / 'work' / 'step1_mesh.npz'); co, pv, tri = d['co'], d['piece'], d['tri']
skin = pv == 0
E = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
E = E[skin[E[:, 0]] & skin[E[:, 1]]]
w = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
G = coo_matrix((np.r_[w, w], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(len(co),) * 2).tocsr()


def bands(dist, ids, step, maxd):
    out = []
    for t in np.arange(0, maxd, step):
        m = ids[(dist[ids] >= t) & (dist[ids] < t + step)]
        if len(m) < 3:
            continue
        c = co[m].mean(0); r = np.median(np.linalg.norm(co[m] - c, axis=1))
        out.append([float(t + step / 2), *np.round(c, 4).tolist(), round(float(r), 4), int(len(m)),
                    round(float(np.ptp(co[m][:, 2])), 3)])
    return out


ids = np.where(skin)[0]
tip = ids[np.argmax(np.linalg.norm(co[ids, :2] - [0, 0], axis=1))]
dt = dijkstra(G, indices=tip)
ax = bands(dt, ids, 0.04, 4.0)
print('TIP', np.round(co[tip], 3))
for b in ax:
    print('AX s %.2f c (%.3f %.3f %.3f) r %.3f n %d zspan %.3f' % tuple(b))
res = {'axial': ax, 'tip': co[tip].tolist()}
# wrists: skin vertices nearest to each hand piece (pieces 5, 6 = the hands with the wrist rings)
for side, hp in (('L', 5), ('R', 6)):
    hand = co[pv == hp]
    kd = cKDTree(hand); dd, _ = kd.query(co[ids])
    seed = ids[dd < np.sort(dd)[12] + 1e-9]
    dw = dijkstra(G, indices=seed, min_only=True)
    arm = bands(dw, ids, 0.03, 0.6)
    print('ARM', side, 'hand piece', hp, 'hand bbox', np.round(hand.min(0), 3), np.round(hand.max(0), 3))
    for b in arm:
        print('  s %.2f c (%.3f %.3f %.3f) r %.3f n %d zspan %.3f' % tuple(b))
    res['arm_' + side] = arm
    res['hand_' + side] = {'piece': hp, 'min': hand.min(0).tolist(), 'max': hand.max(0).tolist()}
(P / 'work' / 'measure.json').write_text(json.dumps(res, indent=1))
