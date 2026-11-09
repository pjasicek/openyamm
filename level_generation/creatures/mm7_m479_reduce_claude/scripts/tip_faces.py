#!/usr/bin/env python3
"""Strand tips of the Treant (twig ends, root-tendril ends, the spire point): the quadric collapse shortens thin
tapered strands (a tip collapse moves the apex along the strand, nearly inside the side planes, so its quadric error is
small): r73 lost 18 cm of a root tendril. Per connected piece, geodesic (edge-graph) distance from the piece's vertex
nearest the trunk axis; tips are local maxima of that distance over a TIP_NBR m neighbourhood, and every face within
TIP_LEN m (geodesic) of a tip is kept exactly. -> work/tips.npy (bool per face). Usage: tip_faces.py [TIP_LEN] [TIP_NBR]"""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
L = float(sys.argv[1]) if len(sys.argv) > 1 else 0.08; NBR = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; n = len(v)
e = np.unique(np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), 1), axis=0)
le = np.linalg.norm(v[e[:, 0]] - v[e[:, 1]], axis=1)
G = coo_matrix((np.r_[le, le], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
_, lab = connected_components(G, directed=False)
axis_d = np.hypot(v[:, 0], v[:, 1] + 0.1)
tip = np.zeros(n, bool); near = np.full(n, np.inf)
for p in np.unique(lab):
    ids = np.flatnonzero(lab == p)
    if len(ids) < 8:
        continue
    sub = G[ids][:, ids]
    base = int(np.argmin(axis_d[ids] + 0.3 * v[ids, 2] * (v[ids, 2] > 1.85)))
    g = dijkstra(sub, indices=base)
    # local maxima of g within NBR geodesic
    loc = dijkstra(sub, limit=NBR, indices=np.argsort(-g)[:min(len(ids), 400)])
    cand = np.argsort(-g)[:min(len(ids), 400)]
    tips = []
    for k, i in enumerate(cand):
        nb = np.isfinite(loc[k])
        if g[i] >= g[nb].max() - 1e-9 and g[i] > NBR:
            tips.append(i)
    if tips:
        dt = dijkstra(sub, limit=L, indices=tips).min(0)
        near[ids] = np.minimum(near[ids], dt); tip[ids[tips]] = True
fk = np.isfinite(near)[f].any(1)
np.save('work/tips.npy', fk); np.save('work/tip_verts.npy', np.flatnonzero(tip))
print('TIPS', int(tip.sum()), 'tip faces', int(fk.sum()), 'of', len(f), 'len', L, 'nbr', NBR)
