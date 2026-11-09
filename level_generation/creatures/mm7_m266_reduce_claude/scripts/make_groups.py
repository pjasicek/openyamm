#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Hydra (m266, faces -y). Materials: Hydra (body, necks, joint lofts; 5,551 faces) and HydraHeads (the five grafted
heads; 12,315 faces). 182 connected pieces: the body with heads 2-5 (9,816 faces), head 1 (1,007), the neck 1 shell
(384) and 179 small pieces (teeth, eyes, tongues, horns, head 1's fin ribs, head 3's crest spikes, head 5's frill,
dorsal and tail spikes).
Labels: 0 body (rest of the budget), 1-5 head k surfaces (HydraHeads faces of pieces over 400 faces, dominant Head<k>),
6 separate pieces of 41-300 faces at least 9 cm long (horns, fin ribs, tongues, frill) decimated on their own
(10 + k for the pieces of head k),
7 the lofts when LOFT_GROUP=1.
Kept exactly: pieces of up to 40 faces (teeth, crest and dorsal spikes) or shorter than 9 cm (eyes, the rest of the
teeth), and the five head-to-neck lofts (Hydra faces with any Head<k> weight).
Usage: make_groups.py [small faces, default 40] [short cm, default 9]  -> also work/face_labels.npz (head k per face,
neck chain owner k per vertex, material per face) for the head-intersection gate."""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
SMALL = int(sys.argv[1]) if len(sys.argv) > 1 else 40
SHORT = float(sys.argv[2]) / 100 if len(sys.argv) > 2 else .09
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
sw = np.load('work/src_weights.npz'); W = sw['weights']; names = [str(x) for x in sw['names']]
mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc)
ext = np.zeros(len(sizes))
for p in np.unique(pc):
    pts = v[np.unique(f[pc == p])]; ext[p] = np.linalg.norm(pts.max(0) - pts.min(0))
dom = info['dom'].astype(str)
headw = np.stack([W[:, names.index(f'Head{k}')] for k in range(1, 6)], 1)
loft = (mat == 0) & (headw[f].max(1).max(1) > .01)
g = np.zeros(len(f), int)
for k in range(1, 6):
    g[(mat == 1) & (sizes[pc] > 400) & (dom == f'Head{k}')] = k
small = (sizes[pc] <= SMALL) | (ext[pc] < SHORT)
g[(sizes[pc] <= 300) & ~small] = 6  # the neck 1 shell (384 faces) stays body
for k in range(1, 6):  # the pieces of head k: label 10 + k
    g[(g == 6) & (dom == f'Head{k}')] = 10 + k
import os
if os.environ.get('LOFT_GROUP') == '1':  # lofts decimated on their own (label 7) instead of kept
    g[loft & ~small] = 7; keep = small
else:
    keep = small | loft
if os.environ.get('SPIKE_GROUP') == '1':  # small pieces at least 9 cm long (crest, dorsal, tail spikes): label 21
    spike = (sizes[pc] <= SMALL) & (ext[pc] >= SHORT) & ~loft
    g[spike] = 21; keep = keep & ~spike
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
# gate labels: head k = HydraHeads faces dominated by Head<k>; chain owner = k for Neck<k>_*/Head<k> dominated vertices
vdom = np.array([names[i] for i in W.argmax(1)])
own = np.zeros(n, int)
for k in range(1, 6):
    own[np.char.startswith(vdom, f'Neck{k}_') | (vdom == f'Head{k}')] = k
part = np.zeros(len(f), int)
for k in range(1, 6):
    part[(mat == 1) & (dom == f'Head{k}')] = k
np.savez('work/face_labels.npz', part=part, chain_owner=own, mat=mat)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in list(range(8)) + list(range(11, 16)) + [21]}, 'keep', int(keep.sum()),
      '(small', int(small.sum()), 'loft', int(loft.sum()), ')', 'heads per part', np.bincount(part).tolist())
