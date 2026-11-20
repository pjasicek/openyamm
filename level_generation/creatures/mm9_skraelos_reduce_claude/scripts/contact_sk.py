#!/usr/bin/env python3
"""Posed contact distances of the installed LOD0 for make_sets_sk.py: per GLB face (work/glb_parts.npz order, Skraelos then
SkraelosHead), the smallest distance over every 2nd frame of every clip and the rest pose from the face's posed centroid and
corners to the nearest posed vertex of (0) the bone hands, (1) the staff, (2) the held skull, (3) the necklace.
Writes work/contact.npz (dmin: faces x 4, m). Usage: contact_sk.py"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(str(HERE / 'before' / 'mm9_skraelos.glb')))
g = np.load(HERE / 'work' / 'glb_parts.npz'); names = [str(x) for x in g['names']]; part = g['part']
Ts = [np.asarray(p['triangles']).reshape(-1, 3) for p in m.primitives[:2]]
nA = len(Ts[0]); assert nA + len(Ts[1]) == len(part)
srcs = ['hands', 'staff', 'heldskull', 'necklace']
dmin = np.full((len(part), len(srcs)), np.inf)


def frame(Ps):
    P = np.concatenate(Ps); n0 = len(Ps[0])
    T = np.r_[Ts[0], Ts[1] + n0]
    X = np.concatenate([P[T].mean(1)[:, None], P[T]], 1).reshape(-1, 3)
    for k, s in enumerate(srcs):
        v = np.unique(T[part == names.index(s)])
        d = cKDTree(P[v]).query(X, distance_upper_bound=0.1)[0].reshape(-1, 4).min(1)
        dmin[:, k] = np.minimum(dmin[:, k], d)


frame([p['positions'] for p in m.primitives[:2]]); nfr = 1
for c in m.clips:
    for t in m.clip_times(c)[::2]:
        frame([np.asarray(x[0], np.float64) for x in m.skinned_positions(m.world(m.sample(c, t)))[:2]]); nfr += 1
np.savez(HERE / 'work' / 'contact.npz', dmin=dmin, srcs=np.array(srcs))
for k, s in enumerate(srcs):
    print('CONTACT', s, {names[p]: int(((part == p) & (dmin[:, k] < 0.02)).sum()) for p in range(len(names)) if names[p] != s}, 'frames', nfr)
