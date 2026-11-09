"""Per-face groups for decimate_tex (REA_GROUPS) and the kept faces (REA_KEEP_FACES) of the Ogre Peasant.
Groups: 1 face/head skin (head texture set on the main piece), 2 left hand, 3 right hand, 4 feet (above the soles),
5 shorts, 6 vest, 7 pack, 8 pack straps, 9 belt, 10 other separate pieces (the large pieces by size); the fingertips (distal finger bones) are
kept: every cut tried (hands 40 %, fingers 65 %) tapered them into points, and so are the toes (their rounded tips
turned into spikes with the feet at 50 %), 0 body skin. Kept exactly: pieces up to 80 faces (hair tufts,
eyes, pack details), the ragged shorts (REA_KEEP_GROUPS, default 5: their tatter tips moved 22 mm even
at 90 %) and the soles (faces below REA_SOLE_M, default 1 cm: foot yaw uses the lowest 5 mm).
Usage: make_groups.py -> work/groups.npy, work/keep.npy"""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; w = np.load('work/weights.npz')
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1)
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); main = np.argmax(sizes)
fw = lambda k: w[k][f].mean(1)
g = np.zeros(len(f), int)
order = np.argsort(-sizes)  # main, vest, shorts... by size: label by position instead (centre height / depth)
g[(fl != main)] = 10
cen = {c: v[f[fl == c]].reshape(-1, 3).mean(0) for c in order[1:7]}
for c, ce in cen.items():
    if sizes[c] <= 80:
        continue
    zr = v[f[fl == c]].reshape(-1, 3)[:, 2]
    lab_ = 5 if zr.min() < .6 else 9 if zr.max() - zr.min() < .12 else 7 if ce[1] > .17 else 8 if ce[1] > .1 else 6
    g[fl == c] = lab_; print('piece', c, sizes[c], 'centre', np.round(ce, 3), '-> group', lab_)
g[(fl == main) & (fw('foot') > .5)] = 4
g[(fl == main) & (fw('hand_L') > .5)] = 2
g[(fl == main) & (fw('hand_R') > .5)] = 3
g[(fl == main) & (u > .5)] = 1
keep = sizes[fl] <= int(os.environ.get('REA_SMALL', '80'))
keep |= np.isin(g, [int(x) for x in os.environ.get('REA_KEEP_GROUPS', '5').split(',') if x])  # shorts: tatter tips
keep |= (fl == main) & (fw('tip') > .3)  # fingertips: any cut tapers them into points
keep |= (fl == main) & (fw('toe') > .3)  # toes: rounded tips turned into spikes at 50 %
keep |= v[f][:, :, 2].max(1) < float(os.environ.get('REA_SOLE_M', '0.01'))
for k in range(11):
    print('group', k, int(((g == k) & ~keep).sum()), 'faces (+', int(((g == k) & keep).sum()), 'kept)')
print('KEPT', int(keep.sum()))
np.save('work/groups.npy', g); np.save('work/keep.npy', keep)
