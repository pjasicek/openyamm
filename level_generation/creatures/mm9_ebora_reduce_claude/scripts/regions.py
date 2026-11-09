"""Faces kept exactly for Ebora's reduction -> work/keep_<label>.npy and a report.
Kept: the whole head texture set (face, hair, hair backs, fringe, side locks, horns, eyes, mouth: the user's face
rounds), optionally the wings (REA_KEEP_WINGS=1), hands and fingers (any corner with hand/finger weight > HANDW),
the torso ring at the neck seam (any corner within NECK_R of a head-set vertex), soles (legs faces below the lowest
point + SOLE_H), small separate pieces (<= SMALL faces). Usage: regions.py <label>"""
import os, sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
label = sys.argv[1]
d = np.load('work/mesh_in.npz'); v, f, mat, hw = d['verts'], d['faces'], d['mat'], d['handw']
HANDW = float(os.environ.get('HANDW', '0.2')); NECK_R = float(os.environ.get('NECK_R', '0.02'))
SOLE_H = float(os.environ.get('SOLE_H', '0.06')); SMALL = int(os.environ.get('SMALL', '80'))
masks = {}
masks['head'] = mat == 1
masks['wings'] = (mat == 3) & (os.environ.get('REA_KEEP_WINGS', '1') == '1')
masks['hands'] = (mat == 0) & (hw[f] > HANDW).any(1)
hv = np.unique(f[mat == 1])
near = cKDTree(v[hv]).query(v)[0] < NECK_R
masks['neck'] = (mat != 1) & (mat != 3) & near[f].any(1)
leg = mat == 2; zmin = v[f[leg]][..., 2].min()
masks['soles'] = leg & (v[f].mean(1)[:, 2] < zmin + SOLE_H)
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
masks['small'] = sizes[fl] <= SMALL
for k in os.environ.get('EXTRA_KEEP', '').split(','):
    if k:
        masks[os.path.basename(k)] = np.load(k)
keep = np.zeros(len(f), bool)
for k, m in masks.items():
    print(f'{k:6s} {int(m.sum()):6d} faces ({int((m & ~keep).sum())} new)')
    keep |= m
print('pieces (>80 faces) by material:')
for c in np.argsort(-sizes)[:40]:
    if sizes[c] > SMALL:
        sel = fl == c; print('  piece', c, sizes[c], 'mat', np.bincount(mat[sel]).argmax(), 'centre', np.round(v[f[sel]].reshape(-1, 3).mean(0), 3))
print('small pieces', int(((sizes > 0) & (sizes <= SMALL)).sum()), 'by material', np.bincount(mat[masks['small']], minlength=4))
np.save(f'work/keep_{label}.npy', keep)
free = ~keep
print('KEEP', int(keep.sum()), 'of', len(f), '; free by material', np.bincount(mat[free], minlength=4))
