#!/usr/bin/env python3
"""Body skin the flaps ride on (a60 gates: the front flap went 4 mm under the cut thigh/belly skin in Walking, Running, Dead and
Death, 0 frames on the installed model): every skin face (label 0) whose centroid comes within D m of a flap vertex (front, back,
lining, rim) in any pose (rest and every clip at 10 Hz, installed GLB), mirrored in x. Writes work/keep_extra_flapc.npy (per
Ghoul_A face). MODE=near (default above) or MODE=closest: per pose, only the skin face holding the closest point to each flap
vertex within D (the face flap_gate.py measures against), plus its edge neighbours. Usage: [MODE=closest] flap_keep.py [D]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
D = float(sys.argv[1]) if len(sys.argv) > 1 else 0.04
import os; MODE = os.environ.get('MODE', 'near')
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from detached_parts_audit import closest_on_triangles  # noqa: E402
m = Model(Glb(str(HERE / 'before' / 'mm9_ghoul.glb')))
lab = np.load(HERE / 'work' / 'labels.npz')['body']
rest = m.skinned_positions(m.world({}))[0]; T = np.asarray(rest[1]).reshape(-1, 3); assert len(T) == len(lab)
flapv = np.unique(T[np.isin(lab, (6, 7, 20, 21))]); skin = np.flatnonzero(lab == 0)
keep = np.zeros(len(T), bool)
poses = [{}] + [(c, t) for c in m.clips for t in np.append(np.arange(0, m.clip_times(c)[-1], 0.1), m.clip_times(c)[-1])]
for p in poses:
    w = m.world({}) if p == {} else m.world(m.sample(p[0], float(p[1])))
    X = m.skinned_positions(w)[0][0]
    cen = X[T[skin]].mean(1)
    if MODE == 'near':
        d, _ = cKDTree(X[flapv]).query(cen)
        keep[skin[d < D]] = True
        continue
    _, near = cKDTree(cen).query(X[flapv], k=12); pts = np.repeat(X[flapv], 12, 0); tri = X[T[skin[near.ravel()]]]
    q, _ = closest_on_triangles(pts, tri[:, 0], tri[:, 1], tri[:, 2])
    dd = np.linalg.norm(pts - q, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(flapv))
    ok = dd[r, b] < D
    keep[skin[near[r, b][ok]]] = True
if MODE != 'near':                                  # edge neighbours
    key = np.round(rest[0], 6); _, tp = np.unique(key, axis=0, return_inverse=True); tp = tp.ravel(); TT = tp[T]
    kv = np.zeros(tp.max() + 1, bool); kv[TT[keep].ravel()] = True
    keep |= (kv[TT].sum(1) >= 2) & (lab == 0)
cen0 = rest[0][T].mean(1); mir = cen0 * [-1, 1, 1]
dist, j = cKDTree(cen0).query(mir[keep]); keep[j[dist < 0.01]] = True
name = 'flapc' if MODE == 'near' else 'flapn'
np.save(HERE / 'work' / f'keep_extra_{name}.npy', keep); print('FLAP KEEP', MODE, D, int(keep.sum()), 'of', int((lab == 0).sum()), 'skin faces')
