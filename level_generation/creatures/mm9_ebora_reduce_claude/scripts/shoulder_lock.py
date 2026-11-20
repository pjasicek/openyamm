"""One drift-lock round limited to the upper torso (Ebora's shoulders: the reduced shoulder skin pulled dark texels from the
strap edge into small dark flecks; the motif areas below may soften by the relaxed brief): source faces within REA_LOCK_R
(0.03 m) of torso faces above z 0.5 with texture drift > 40 and area > 1 cm2 are kept.
Usage: shoulder_lock.py <base keep .npy> <out .npy> <tag>"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
base, out, tag = sys.argv[1:4]; R = float(os.environ.get('REA_LOCK_R', '0.03'))
src = np.load('work/mesh_in.npz'); scen = src['verts'][src['faces']].mean(1); smat = src['mat']
keep = np.load(base).copy(); n0 = int(keep.sum()); tree = cKDTree(scen)
d = np.load(f'work/mesh_{tag}.npz'); dr = np.load(f'work/drift_{tag}.npy'); tri = d['verts'][d['faces']]
m = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
hits = np.flatnonzero((m == 0) & (tri.mean(1)[:, 2] > 0.5) & (dr > 40) & (area > 1e-4))
for i in hits:
    for p in [*tri[i], tri[i].mean(0)]:
        idx = np.array(tree.query_ball_point(p, R), int); keep[idx[smat[idx] == 0]] = True
np.save(out, keep); print('SHOULDER LOCK', len(hits), 'drifted faces;', n0, '->', int(keep.sum()), 'kept')
