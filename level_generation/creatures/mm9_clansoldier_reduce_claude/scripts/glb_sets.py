#!/usr/bin/env python3
"""Sets for mpqem.py per GLB LOD0 face (work/mesh_in.npz keeps the GLB face order: checked, centroids match index for index):
keep = work/keep_<KEEP>.npy (make_sets.py: face/neck/eyes, sleeve-end rings, graft junction, grip contact, 2nd/3rd phalanges, soles,
waist lap, small pieces, weapons), group = work/groups_<KEEP>.npy (1 hands, 2 helmet, 3 skirt outer, 5 boots, 6 pants; 0 coat/sash),
lining = every lining face (skirt and sleeve ends: finish_clan.py's inner copies), lined = the outer faces they line (the skirt
outer and the sleeve-end rings). mpqem.py re-emits the linings as reversed twins of the surviving lined faces.
Usage: glb_sets.py <keep tag> <out tag> -> work/glb_sets_<out tag>.npz"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
W = Path(__file__).resolve().parents[1] / 'work'
k = sys.argv[1]
keep = np.load(W / f'keep_{k}.npy').astype(bool); group = np.load(W / f'groups_{k}.npy').astype(int)
lab = np.load(W / 'face_labels.npz'); part, lining, cen = lab['part'], lab['lining'].astype(bool), lab['cen']
sl = (part == 1) & lining
outer1 = np.flatnonzero((part == 1) & ~lining)
dd, nn = cKDTree(cen[outer1]).query(cen[sl])          # each sleeve lining face's own outer face (3 mm out)
lined = (part == 7) & ~lining
lined[outer1[nn]] = True
print('sleeve lining -> outer', int(sl.sum()), 'matched', len(np.unique(nn)), 'max dist mm', round(float(dd.max()) * 1000, 2))
group[keep] = 0; group[lining] = 0
np.savez(W / f'glb_sets_{sys.argv[2]}.npz', keep=keep, group=group, lining=lining, lined=lined)
print('SETS', sys.argv[2], 'keep', int(keep.sum()), 'lining', int(lining.sum()), 'lined', int(lined.sum()), 'lined kept', int((lined & keep).sum()),
      'groups free', {int(g): int(((group == g) & ~keep & ~lining).sum()) for g in np.unique(group)})
