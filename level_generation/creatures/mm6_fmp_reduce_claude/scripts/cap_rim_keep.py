"""Keep the hair faces within R metres of the cap (piece 13) exactly: the hair under the cap is painted cap-blue, and
a cut there pushes it out below the rim. Usage: cap_rim_keep.py <keep in> <keep out> [R=0.025]"""
import sys, numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); comp = np.load('work/comp.npy')
R = float(sys.argv[3]) if len(sys.argv) > 3 else 0.025
cap = np.unique(d['faces'][comp == 13]); tree = cKDTree(d['verts'][cap])
hair = np.isin(comp, [11, 12, 16])
dist = np.min([tree.query(d['verts'][d['faces'][:, k]])[0] for k in range(3)], axis=0)
keep = np.load(sys.argv[1]) | (comp == 13) | (hair & (dist < R))
np.save(sys.argv[2], keep); print('rim hair kept', int((hair & (dist < R)).sum()), 'of', int(hair.sum()), 'total keep', int(keep.sum()))
