#!/usr/bin/env python3
"""Keep / group sets per face of work/mesh_in.npz for decimate_tex.py, from work/labels.npz (labels.py, skin_split.py, hand_thick.py).
Kept exactly (prio-1 relaxed set): face front (reg 4: eyes, brows, nose, mouth, lips, ears, jaw, chin, beard), head-set skin outside
the face box in clusters of >= CLUSTER faces (reg 9: nape, neck, ear backs), tusks, the neck seam (head-set faces within 2 rings of the
body material), the fingers (hand faces thinner than 4.5 cm: every finger whole), the grip contact (hand faces within 1.5 cm of the
club), the hand-graft junction, soles (lowest 2 cm) and the club (rebuilt separately by club_rebuild.py).
Groups (REA_GROUP_RATIOS): 1 hair (reg 5 + speckles of reg 9), 2 palm and back of hand, 3 wrist cuffs; 0 = body skin (ladder budget).
Usage: make_sets.py <tag> -> work/keep_<tag>.npy, work/groups_<tag>.npy"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
tag = sys.argv[1]; CL = int(os.environ.get('CLUSTER', 8))
d = np.load(HERE / 'work/mesh_in.npz'); V, F = d['verts'], d['faces']; L = np.load(HERE / 'work/labels.npz'); reg = L['reg']
# reg 9 clusters (faces sharing an edge)
s9 = np.where(reg == 9)[0]; e = {}
for i in s9:
    for a, b in ((0, 1), (1, 2), (2, 0)):
        e.setdefault(tuple(sorted((F[i, a], F[i, b]))), []).append(i)
loc = {f: k for k, f in enumerate(s9)}; r, c = [], []
for fs in e.values():
    for a in fs:
        for b in fs:
            if a != b: r.append(loc[a]); c.append(loc[b])
_, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(len(s9), len(s9))), directed=False)
big = np.zeros(len(F), bool); big[s9] = np.bincount(lab)[lab] >= CL
keep = (reg == 4) | big | (reg == 7) | L['seam'] | L['hthin'] | L['grip'] | L['junction'] | L['sole'] | (reg == 8)
groups = np.zeros(len(F), int)
groups[((reg == 5) | ((reg == 9) & ~big)) & ~keep] = 1
groups[(reg == 2) & ~keep] = 2
groups[(reg == 3) & ~keep] = 3
names = {0: 'body', 1: 'hair', 2: 'palm/back', 3: 'cuffs'}
for k, n in names.items(): print(f'group {k} {n:10s} {int(((groups == k) & ~keep).sum()):6d}')
print('kept: face', int((reg == 4).sum()), 'skin clusters', int(big.sum()), 'speckles', int(((reg == 9) & ~big).sum()), 'tusks', int((reg == 7).sum()),
      'seam', int(L['seam'].sum()), 'fingers', int(L['hthin'].sum()), 'grip', int(L['grip'].sum()), 'junction', int(L['junction'].sum()),
      'soles', int(L['sole'].sum()), 'club', int((reg == 8).sum()))
print('TOTAL keep', int(keep.sum()), 'free', int((~keep).sum()), f'protected share {keep.mean():.3f}')
np.save(HERE / 'work' / f'keep_{tag}.npy', keep); np.save(HERE / 'work' / f'groups_{tag}.npy', groups)
lv = np.where(keep, 7, 0); lv[keep & ((reg == 4) | big | (reg == 7))] = 4; lv[(groups == 1) & ~keep] = 5; lv[(groups == 2) & ~keep] = 2; lv[(groups == 3) & ~keep] = 6
np.save(HERE / 'work' / f'lab_sets_{tag}.npy', lv)
