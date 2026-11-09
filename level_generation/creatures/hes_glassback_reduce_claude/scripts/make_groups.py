#!/usr/bin/env python3
"""Keep set and groups of the Glassback (work/mesh_in.npz order). Kept exactly: the head texture set (u > 1024/2080 of
the merged atlas: head, beak, both eyeballs) and the feet (faces dominated by Foot_* joints: the glass toes, the
soles the stride and floor gates measure). GROUPS (env, optional) e.g. 'legs' puts Upper/Lower leg faces in group 1,
'tail' Tail* in group 2, 'neck' Neck1 in group 3. -> work/keep.npy, work/groups.npy"""
import os
import numpy as np
m = np.load('work/mesh_in.npz'); fi = np.load('work/faces_info.npz'); dom = fi['dom']
u = m['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1)
head = u > 1024 / 2080
feet = np.char.startswith(dom.astype(str), 'Foot_')
keep = head | feet
if os.environ.get('KEEP_EXTRA'):
    keep |= np.load(os.environ['KEEP_EXTRA'])
g = np.zeros(len(u), int)
want = os.environ.get('GROUPS', '').split(',')
if 'legs' in want:
    g[np.char.startswith(dom.astype(str), 'Upper_') | np.char.startswith(dom.astype(str), 'Lower_')] = 1
if 'tail' in want:
    g[np.char.startswith(dom.astype(str), 'Tail')] = 2
if 'neck' in want:
    g[dom == 'Neck1'] = 3
g[keep] = -1
np.save('work/keep.npy', keep); np.save('work/groups.npy', g)
print('KEEP', int(keep.sum()), '(head', int(head.sum()), 'feet', int((feet & ~head).sum()), ') GROUPS',
      {k: int((g == k).sum()) for k in range(-1, 4)})
