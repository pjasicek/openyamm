#!/usr/bin/env python3
"""Per-face labels of the dumped installed mesh (work/mesh_in.npz) from Kira's master (work/master_labels.npz, dump_master_labels.py):
the installed GLB was exported from mm9_kira_claude/work/uv_v6.blend in the same local frame, so each triangle's centroid matches one
master face. -> work/faces_info.npz (part, hand, mat, match distance). Parts: 0 MPFB hands, 1 armour shell (cuirass, sleeves,
vambraces, the two wrist rim caps), 5 legs and boots, 7 mail skirt, 9 belt, 10 medallion, 11 knee cops, 12 pauldron lames,
13 tasset, 20 face and neck skin, 21 hair, 22 eyes, 23 braid."""
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); m = np.load('work/master_labels.npz')
c = d['verts'][d['faces']].mean(1)
dist, j = cKDTree(m['cen']).query(c)
mat = (d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1) // 2).astype(int)
print('MATCH max mm', round(dist.max() * 1000, 4), 'unique', len(np.unique(j)), 'of', len(c), 'material agree', bool((m['mat'][j] == mat).all()))
part = m['f_part'][j]; hand = m['f_hand'][j]
np.savez('work/faces_info.npz', part=part, hand=hand, mat=mat, dist=dist)
u, n = np.unique(part, return_counts=True); print('PARTS', dict(zip(u.tolist(), n.tolist())))
