#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_small.npy).
MM7 Ghost (m242, faces -y, 1.86 m), 207 connected pieces from the welded export:
- 1 skull (the largest B_Head piece: face, sockets, teeth, jaw; 1,100 faces): its own gentle ratio (REA skull);
- 2 cape/hood shell (the B_Head-dominated piece that reaches below the shoulders, 900 faces);
- 0 trunk and arm bones (the ladder's free part; rigid pieces of > MIN faces on the spine, pelvis, neck, clavicles, upper arms, forearms):
  ribcage halves, sternum, vertebral column, humeri;
- 4 robe shreds (pieces dominated by a Robe_* chain bone) of > MIN faces;
- kept exactly: every piece of <= MIN faces (phalanges, claw tips, teeth fragments, short shreds) and every piece on a
  hand or finger bone (the claws: rigid, thin, their tips taper at any cut), and every non-rigid bone piece (dominant
  bone under MIXED_SHARE of its faces: sternum, front rib bands, vertebral column).
Label 0 (the rest) takes the remaining ladder budget."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
MIN = int(os.environ.get('MIN_FACES', '30'))
MIXED_SHARE = float(os.environ.get('MIXED_SHARE', '0.9'))
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); dom = info['dom'].astype(str)
g = np.zeros(len(f), int); keep = np.zeros(len(f), bool)
head_pieces = []
for p in np.unique(pc):
    sel = pc == p; vals, cnt = np.unique(dom[sel], return_counts=True); dm = vals[cnt.argmax()]
    vv = v[np.unique(f[sel])]
    if dm == 'B_Head':
        head_pieces.append((sizes[p], p, vv[:, 2].min()))
    if sizes[p] <= MIN or 'Hand' in dm or 'Finger' in dm:
        keep[sel] = True
    elif dm.startswith('Robe_'):
        g[sel] = 4
    elif any(k in dm for k in ('Spine', 'Pelvis', 'Neck', 'Clavicle', 'UpperArm', 'Forearm')):
        g[sel] = 0                                  # trunk/arm bones: label 0 takes the ladder's remaining budget
        # bone pieces that are not rigid (the sternum and the front rib bands carry a spine weight gradient, some a
        # Robe_CF_1 share): longer reduced edges span more of the gradient (bone stretch 1.29 -> 1.85): keep them
        if cnt.max() < MIXED_SHARE * sel.sum() and dm != 'B_Head':
            keep[sel] = True
for size, p, zmin in sorted(head_pieces, reverse=True):
    if size <= MIN:
        continue
    if size == max(h[0] for h in head_pieces if h[2] < 1.2) and zmin < 1.2:
        g[pc == p] = 2                            # the cape/hood shell (reaches the hips)
    elif zmin >= 1.2:
        g[pc == p] = 1                            # skull pieces stay above the neck
    # anything else on the head (the vertebral column, mixed head/spine weights) stays with the bones (label 0)
keep &= g == 0
print('MIXED bone pieces kept', int((keep & (g == 0)).sum()))
np.save('work/groups.npy', g); np.save('work/keep_small.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(5)}, 'kept', int(keep.sum()), 'of', len(f))
