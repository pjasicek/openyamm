#!/usr/bin/env python3
"""Variant g of make_groups.py (run it first): also keeps the trouser and skin faces within 3 cm of the rope exactly
(cr74 pushed trouser-top wedges out over the rope at the back and sides) and gives the trouser faces with wound
texels (the holes and the bloody right cuff) their own group 5. -> work/keep_g.npy, work/groups_g.npy"""
import numpy as np
from scipy.spatial import cKDTree
L = np.load('work/face_labels.npz', allow_pickle=True); d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
P = L['piece']; rope = np.isin(P, [4, 5])
dist, _ = cKDTree(v[np.unique(f[rope])]).query(v[f].mean(1))
keep = np.load('work/keep.npy') | (np.isin(P, [0, 1]) & (dist < 0.03))
g = np.load('work/groups.npy'); g[(P == 1) & (L['wound'] > 0)] = 5; g[keep] = -1
np.save('work/keep_g.npy', keep); np.save('work/groups_g.npy', g)
print('KEEP', int(keep.sum()), 'GROUPS', {k: int((g == k).sum()) for k in range(6)})
