#!/usr/bin/env python3
"""Keep set and per-part groups of the drone (work/mesh_in.npz order) from the master's face labels
(work/master_labels.npz: mat/part of ../hes_drone_claude/work/uv3d.npz matched by face centre) and the welded pieces
(work/piece.npy). Kept exactly: the Glow material (lens dome, vent nozzle and slots), the bone ribs and tail hooks
(silhouette), the trailing cables and their gold plugs (thin 6-sided tubes) and, with KEEP_TUBES=1, the resin tubes.
Groups: 1 resin tubes, 2 the five raised plates, 3 chitin masses, 4 the vent drum's band and rims; 0 the lathed
shell (collar, casing, tail). -> work/keep.npy, work/groups.npy"""
import os
import numpy as np
m = np.load('work/mesh_in.npz'); L = np.load('work/master_labels.npz'); pc = np.load('work/piece.npy')
mat, part = L['mat'], L['part']
glow = m['wuv'].reshape(-1, 3, 2)[:, 0, 0] >= 2
cnt = np.bincount(pc); size = cnt[pc]
keep = glow | (mat == 8) | (mat == 9) | (part >= 1) & (part <= 3)
g = np.zeros(len(mat), int)
g[mat == 6] = 1
plate_pieces = [p for p in np.unique(pc) if cnt[p] == 88]
g[np.isin(pc, plate_pieces)] = 2
g[mat == 7] = 3
drum = pc == np.bincount(pc[mat == 4]).argmax(); g[drum & ~glow] = 4
if os.environ.get('KEEP_TUBES') == '1':
    keep |= g == 1
g[keep] = -1
np.save('work/keep.npy', keep); np.save('work/groups.npy', g)
print('KEEP', int(keep.sum()), 'GROUPS', {k: int((g == k).sum()) for k in range(-1, 5)})
