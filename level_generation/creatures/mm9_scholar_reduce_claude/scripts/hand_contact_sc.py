#!/usr/bin/env python3
"""Robe faces the hands rest on (Scholar copy of the Monk's hand_contact.py; Fidget: the left hand rests on the stole and
medallion): every Scholar_A face of the installed LOD0 whose posed centroid comes within R m of a posed hand vertex in any
frame (every 2nd frame) of every clip, mirrored by x position onto the other side. Writes a GLB-face mask over
work/glb_parts.npz order (Scholar_A then ScholarHead). Usage: hand_contact_sc.py <out .npy>   (env R, default 0.02)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.02'))
m = Model(Glb(str(HERE / 'before' / 'mm9_scholar.glb')))
g = np.load(HERE / 'work' / 'glb_parts.npz'); names = [str(x) for x in g['names']]
T = np.asarray(m.primitives[0]['triangles']).reshape(-1, 3); nA = len(T)
part = g['part'][:nA]; assert (g['mat'][:nA] == 0).all()
hand_v = np.unique(T[part == names.index('hands')]); target = part == names.index('robe')
hit = np.zeros(nA, bool)
for c in m.clips:
    for t in m.clip_times(c)[::2]:
        P = np.asarray(m.skinned_positions(m.world(m.sample(c, t)))[0][0])
        d, _ = cKDTree(P[hand_v]).query(P[T].mean(1), distance_upper_bound=R)
        h = target & (d < R)
        if h.sum() > (hit | h).sum() - hit.sum() and h.any():
            pass
        hit |= h
print('contact faces', int(hit.sum()))
cen = g['cen'][:nA]
mir = cKDTree(cen[target] * [-1, 1, 1]).query(cen[hit])[1]   # mirror partner of every hit (nearest mirrored robe centroid)
tidx = np.flatnonzero(target)
hit2 = hit.copy(); hit2[tidx[cKDTree(cen[target]).query(cen[hit] * [-1, 1, 1])[1]]] = True
out = np.zeros(len(g['part']), bool); out[:nA] = hit2
np.save(HERE / sys.argv[1], out); print('HANDCONTACT', int(hit.sum()), 'mirrored', int(hit2.sum()))
