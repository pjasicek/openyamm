#!/usr/bin/env python3
"""Per-face regions of the m230 plate fighter rest mesh (work/mesh_in.npz, work/groups.npz) by connected piece ->
work/regions.npy: 1 body plates (cuirass, tabard, thigh/leg plates, arms, sabatons), 2 helm (largest head-atlas piece),
3 eagle crest (head-atlas piece on the helm top), 4 plume strands (other head-atlas pieces), 5 gauntlets (pieces
dominated by hand/finger weights), 8 small pieces (<= 80 faces). work/soles.npy: faces below 6 cm.
work/hand.npy: faces touching a vertex with hand + finger weight > 0.3 (the fitted sword grip and the cuffs)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; n = len(v)
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
uv = d['wuv'].reshape(-1, 3, 2); headuv = uv[..., 0].mean(1) > 0.5
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); c = v[f].mean(1)
handw = W[:, [i for i, x in enumerate(names) if x.endswith('_Hand') or 'Finger' in x]].sum(1)
reg = np.ones(len(f), int)
headp = [p for p in np.flatnonzero(sizes) if headuv[fl == p].mean() > .5]
helm = max(headp, key=lambda p: sizes[p])
for p in np.flatnonzero(sizes):
    m = fl == p
    if sizes[p] <= 80:
        reg[m] = 8
    elif p == helm:
        reg[m] = 2
    elif p in headp:
        vs = np.unique(f[m]); span = np.ptp(v[vs][:, 2])
        reg[m] = 3 if span < 0.2 else 4  # crest sits on the helm top; plume strands run 0.3-0.4 m down the back
    elif handw[np.unique(f[m])].mean() > .3:
        reg[m] = 5
soles = c[:, 2] < 0.06
hand = (handw[f] > 0.3).any(1)
np.save('work/regions.npy', reg); np.save('work/soles.npy', soles); np.save('work/hand.npy', hand)
nm = {1: 'body', 2: 'helm', 3: 'crest', 4: 'plume', 5: 'gauntlets', 8: 'small'}
print({nm[k]: int((reg == k).sum()) for k in nm}, 'soles', int(soles.sum()), 'hand faces', int(hand.sum()),
      'gauntlet faces not hand', int(((reg == 5) & ~hand).sum()))
