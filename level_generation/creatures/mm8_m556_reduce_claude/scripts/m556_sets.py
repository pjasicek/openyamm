"""Wasp keep set and region labels from the rest mesh (work/mesh_in.npz) and dominant bones (work/domgroup.npz).
Kept exactly: antennae, mandibles, middle legs, the small joint balls, and the arm faces dominated by Hand/Claw bones
(sword and shield grips). Groups: 2 wings, 3 hind legs, 4 upper/fore arms; 0 the trunk (head handled by
REA_PROTECT_HEAD). Writes work/keep_b.npy, work/groups_b.npy; prints counts."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
g = np.load('work/domgroup.npz'); dom = g['dom']; names = [str(x) for x in g['names']]
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]


def face_bone(i):
    b = [names[dom[x]] for x in f[i]]
    return max(set(b), key=b.count)


fb = np.array([face_bone(i) for i in range(len(f))])
piece_major = {}
for c in np.unique(fl):
    bs = fb[fl == c]; u, k = np.unique(bs, return_counts=True); piece_major[c] = u[np.argmax(k)]
pm = np.array([piece_major[c] for c in fl])
size = np.bincount(fl)[fl]
keep = np.zeros(len(f), bool); grp = np.zeros(len(f), int)
keep |= np.char.startswith(pm.astype(str), 'Antenna') | np.char.startswith(pm.astype(str), 'Mandible')
keep |= np.char.startswith(pm.astype(str), 'Mid')                     # middle legs (thin) and their joint balls
keep |= size <= 200                                                     # joint balls
arm = np.isin(pm, ['Claw3_L', 'Claw3_R', 'Hand_L', 'Hand_R', 'Claw1_L', 'Claw1_R'])
keep |= arm & (np.char.startswith(fb.astype(str), 'Claw') | np.char.startswith(fb.astype(str), 'Hand'))
grp[np.char.startswith(pm.astype(str), 'Wing')] = 2
grp[np.char.startswith(pm.astype(str), 'Hind') & (size > 200)] = 3
grp[arm & ~keep] = 4
keep |= np.char.startswith(pm.astype(str), 'Wing')                    # thin leaf membranes: any cut notches the outline
keep |= np.char.startswith(fb.astype(str), 'HindTarsus')                # segmented tarsus beads
keep |= (fb == 'Abdomen4')                                              # stinger and its base bead
grp[keep] = 0
np.save('work/keep_b.npy', keep); np.save('work/groups_b.npy', grp)
print('KEEP', int(keep.sum()), 'GROUPS', {k: int((grp == k).sum()) for k in (2, 3, 4)},
      'FREE+HEAD', int(((grp == 0) & ~keep).sum()), 'of', len(f))
