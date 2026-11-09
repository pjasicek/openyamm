#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep / protect masks.
MM7 Harpy (m262, faces -y, 2.2 m with the raised wings). Pieces (connected components of the welded source):
14 skin (head, torso, arms, thighs; its head-set faces are the face and scalp), 15/18 hands with fingers, 16/17 legs
and talons, 22/23 bracers, 24/28 the wing sheets, 86/87 eyes, 89-100 the long hair (head texture set, on B_Head and
B_Spine1), and ~80 feather cards (wings, tail) of <= 80 faces.
Labels: 0 rest (torso, arms, thighs, legs), 1 hair (pieces in the head set other than the skin and eyes), 2 hand
backs/palms (B_*_Hand dominant), 3 talons and feet (B_*_Toe0 / B_*_Foot), 4 wing sheets (pieces > 80 faces dominated
by a Wing bone), 5 feather cards (wing/tail pieces <= 100 faces), 6 feathered thighs and shins (B_*_Thigh/Calf).
work/keep_cards.npy: keep.npy plus every feather card.
work/keep.npy (exact): eyes and the other small head-set pieces under 30 faces, the bracers, every finger-dominated
face (the knife fist), every other small piece that is not a feather card (fittings).
work/protect_face.npy: head-set faces of the skin piece (face and scalp), decimated gently on their own
(REA_PROTECT_RATIO)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc)
dom = info['dom'].astype(str); head = info['u'] > 0.505
skin = np.argmax(sizes)
piece_dom = {}
for p in np.unique(pc):
    vals, cnt = np.unique(dom[pc == p], return_counts=True); piece_dom[p] = vals[cnt.argmax()]
psize = sizes[pc]; pdom = np.array([piece_dom[p] for p in pc])
headset_piece = np.array([head[pc == p].all() for p in range(len(sizes))])[pc]
small = psize <= 80
feather = (psize <= 100) & ~headset_piece & (np.char.startswith(pdom, 'Wing') | (pdom == 'B_Tail'))   # tail cards up to 87 faces
finger = np.char.find(dom, 'Finger') >= 0
bracer = np.isin(pc, [22, 23]) & False
for p in np.unique(pc):                                      # bracers: the hand-adjacent pieces of 100-200 faces
    if 100 <= sizes[p] <= 200 and any(k in piece_dom[p] for k in ('Forearm', 'Hand')):
        bracer |= pc == p
g = np.zeros(len(f), int)
g[headset_piece & (pc != skin) & (psize > 30)] = 1
g[np.isin(dom, ['B_L_Hand', 'B_R_Hand']) & ~bracer & (pc != skin)] = 2
g[np.isin(dom, ['B_L_Toe0', 'B_R_Toe0', 'B_L_Foot', 'B_R_Foot'])] = 3
g[(psize > 80) & np.char.startswith(pdom, 'Wing')] = 4
g[feather] = 5
g[(g == 0) & np.isin(dom, ['B_L_Thigh', 'B_R_Thigh', 'B_L_Calf', 'B_R_Calf'])] = 6
keep = (headset_piece & (pc != skin) & (psize <= 30)) | bracer | finger | (small & ~feather & ~headset_piece)
keep_cards = keep | feather                                     # variant: every feather card exact
protect = head & (pc == skin)
g[keep | protect] = -1
np.save('work/groups.npy', g); np.save('work/keep.npy', keep); np.save('work/keep_cards.npy', keep_cards); np.save('work/protect_face.npy', protect)
print('GROUPS', {k: int((g == k).sum()) for k in (0, 1, 2, 3, 4, 5, 6)}, 'kept', int(keep.sum()), 'protected face',
      int(protect.sum()), 'bracer faces', int(bracer.sum()), 'finger faces', int(finger.sum()))
