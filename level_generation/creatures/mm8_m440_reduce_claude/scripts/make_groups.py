"""Per-face groups for decimate_tex (REA_GROUPS) and the kept faces (REA_KEEP_FACES) of the Ogre Warrior.
Groups: 1 face/scalp/neck skin (head texture set of the main piece), 2 left hand, 3 right hand (the club grip: kept,
as in every production LOD), 4 feet above the soles without the toes, 5 helmet dome and crest, 7 horns (head set
pieces), 6 armour and cloth pieces (straps, belt, shoulder plate, wrist and shin wraps, apron), 8 mouth pieces
(teeth rows, lips), 9 the helmet crest's ten rivets (70 faces each), 0 body skin (torso, arms, legs). Kept exactly: pieces up to
REA_SMALL faces (rivets, tusks), the eyes, the fingertips (distal finger bones; any cut tapers them into points),
the toes, the soles (faces below REA_SOLE_M; foot yaw uses the lowest 5 mm) and REA_KEEP_GROUPS (default 3,8).
Usage: make_groups.py -> work/groups.npy, work/keep.npy"""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; w = np.load('work/weights.npz')
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1); head_set = u > 1056 / 2080
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); main = np.argmax(sizes)
fw = lambda k: w[k][f].mean(1)
SMALL = int(os.environ.get('REA_SMALL', '80'))
g = np.zeros(len(f), int); keep = sizes[fl] <= SMALL
for c in np.unique(fl):
    m = fl == c
    if c == main:
        continue
    p = v[f[m]].reshape(-1, 3); ext = p.max(0) - p.min(0)
    if sizes[c] <= SMALL:
        if head_set[m].mean() > .5 and sizes[c] >= 60 and ext.max() < .02:
            g[m] = 9; keep &= ~m  # the helmet crest's rivets: 70-faced 1.4 cm domes (the brim's are 24)
        continue
    if head_set[m].mean() > .5:
        if ext.max() < .05 and p[:, 2].min() > 1.5:
            keep |= m; kind = 'eye (kept)'
        elif p[:, 2].max() < 1.49 and p[:, 1].max() < 0:
            g[m] = 8; kind = 'mouth'
        elif abs(p[:, 0].mean()) > .07:
            g[m] = 7; kind = 'horn'
        else:
            g[m] = 5; kind = 'helmet'
    elif fw('hand_L')[m].mean() > .5:
        g[m] = 2; kind = 'left hand'
    elif fw('hand_R')[m].mean() > .5:
        g[m] = 3; kind = 'right hand'
    elif fw('foot')[m].mean() > .5:
        g[m] = 4; kind = 'foot'
    elif sizes[c] > 1000:
        kind = 'legs (body skin)'
    else:
        g[m] = 6; kind = 'gear'
    print('piece', c, sizes[c], kind, 'z', round(float(p[:, 2].min()), 3), '-', round(float(p[:, 2].max()), 3))
g[(fl == main) & head_set] = 1
keep |= np.isin(g, [int(x) for x in os.environ.get('REA_KEEP_GROUPS', '3,8').split(',') if x])
keep |= fw('tip') > .3
keep |= fw('toe') > .3
keep |= v[f][:, :, 2].max(1) < float(os.environ.get('REA_SOLE_M', '0.01'))
for k in range(10):
    print('group', k, int(((g == k) & ~keep).sum()), 'faces (+', int(((g == k) & keep).sum()), 'kept)')
print('KEPT', int(keep.sum()))
np.save('work/groups.npy', g); np.save('work/keep.npy', keep)
