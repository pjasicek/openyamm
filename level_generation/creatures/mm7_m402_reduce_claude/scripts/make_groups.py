#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Spider (m402, faces -y). Pieces (after the weld): the body (cephalothorax + abdomen, 3,047 faces), eight legs
(859-1,111 faces each), four chelicera/fang pieces (187-266), four eyes (~50), two palp-like pieces (176, 286) and
the red hair-fringe cards (12-110). Labels: 0 body, 1 legs (Femur/Tibia/Tarsus on the eight leg pieces), 2 other
pieces over 80 faces (fringe cards, palps).
Kept exactly: the chelicerae and fangs (Fang-dominated pieces over 150 faces), the eyes, and every piece of up to
80 faces (thin fringe tips taper into points at any cut)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); body = np.argmax(sizes)
dom = info['dom'].astype(str)
psize = sizes[pc]
leg_piece = (psize > 800) & (pc != body)
g = np.zeros(len(f), int)
g[leg_piece] = 1
g[(pc != body) & ~leg_piece] = 2
fang_piece = np.zeros(len(f), bool)
for p in np.unique(pc[(psize > 150) & (psize < 800)]):
    sel = pc == p
    if np.char.startswith(dom[sel], 'Fang').mean() > .5:
        fang_piece |= sel
keep = fang_piece | ((pc != body) & (psize <= 80))
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep); np.save('work/face_piece.npy', pc)  # pieces for card_list.py
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(3)}, 'keep', int(keep.sum()))
