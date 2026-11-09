"""Add the bodice's centre-front lacing strip (main body faces with |x| < REA_LACE_X, front, 0.95-1.38 m) and both
bracers to a keep set: the painted lacing line bends into a zigzag under any collapse, bracer rims turn jagged.
Usage: keep_lacing.py <base keep .npy> <out .npy>"""
import os, sys
import numpy as np
d = np.load('work/mesh_in.npz'); c = d['verts'][d['faces']].mean(1)
comp = np.load('work/components.npy'); keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum())
hx = float(os.environ.get('REA_LACE_X', '0.03'))
lace = (comp == 0) & (np.abs(c[:, 0]) < hx) & (c[:, 1] < -0.04) & (c[:, 2] > 0.95) & (c[:, 2] < 1.38)
keep |= lace | np.isin(comp, [15, 8])
np.save(sys.argv[2], keep); print('LACE', int(lace.sum()), 'KEEP', n0, '->', int(keep.sum()))
