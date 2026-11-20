#!/usr/bin/env python3
"""Keep and group masks per rest triangle of work/source.blend (work/faces_info.npz) -> work/keep.npy, work/groups.npy.
Kept exactly: Head (face set), Neck (gap tuck, colour fade), both hair primitives (lofted spikes on chains), hands with
claws and fingers (dominant Zhand*/Zfing* bones), and the sleeve faces within CUFF m of the wrist rim (the wrist sits
inside the cuff; its print is kept). Every other primitive is decimated on its own (group = material index + 1), so
primitive borders stay where they are. Usage: masks.py [cuff metres, default 0.045]"""
import sys
import collections
import numpy as np
from scipy.spatial import cKDTree
CUFF = float(sys.argv[1]) if len(sys.argv) > 1 else 0.045
d = np.load('work/faces_info.npz'); names = d['names']; F = d['faces']; mat = d['mat']; dom = d['dom']; V = d['verts']
mats = list(d['mats'])
ishand = np.array([n.startswith('Zhand') or n.startswith('Zfing') for n in names]); fh = ishand[dom][F].mean(1) > 0.5
keep = np.isin(mat, [mats.index(m) for m in ('BansheeHead', 'BansheeNeck', 'BansheeHairL', 'BansheeHairR')])
for arm in ('BansheeArmL', 'BansheeArmR'):
    sel = mat == mats.index(arm)
    keep |= sel & fh
    sleeve = np.where(sel & ~fh)[0]
    E = collections.Counter(tuple(sorted(e)) for f in F[sleeve] for e in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])))
    rim = np.unique([e for e, c in E.items() if c == 1])
    hv = np.unique(F[sel & fh]); dh = cKDTree(V[hv]).query(V[rim])[0]
    rim = rim[dh < 0.06]                       # the wrist loop (the shoulder loop is far from the hand)
    near = cKDTree(V[rim]).query(V[F[sleeve]].reshape(-1, 3))[0].reshape(-1, 3).min(1) < CUFF
    keep[sleeve[near]] = True
    print(arm, 'hand', int((sel & fh).sum()), 'cuff kept', int(near.sum()), 'sleeve free', int((~near).sum()))
groups = np.where(keep, 0, mat + 1)
np.save('work/keep.npy', keep); np.save('work/groups.npy', groups)
print('KEEP', int(keep.sum()), 'of', len(F), {mats[g - 1]: int((groups == g).sum()) for g in np.unique(groups) if g})
