"""Inverted faces of a decimated mesh: normal against the nearest source faces' normals (either winding of a
two-sided pair counts as a match). Prints count, area and positions; writes work/flipped_<tag>.npy.
Usage: flip_check.py <tag, e.g. r70>"""
import sys
import numpy as np
from scipy.spatial import cKDTree


def faces(path):
    d = np.load(path); t = d['verts'][d['faces']]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); a = np.linalg.norm(n, axis=1)
    return t.mean(1), n / (a[:, None] + 1e-12), a / 2


tag = sys.argv[1]
sc, sn, _ = faces('work/mesh_in.npz'); cc, cn, ca = faces(f'work/mesh_{tag}.npz')
dist, idx = cKDTree(sc).query(cc, 6)
best = (sn[idx] * cn[:, None]).sum(-1).max(1)  # best agreement among the 6 nearest source faces
flip = best < -0.3
np.save(f'work/flipped_{tag}.npy', flip)
print(tag, 'flipped', int(flip.sum()), 'area cm2', round(float(ca[flip].sum() * 1e4), 2))
for i in np.argsort(-ca * flip)[:8]:
    if flip[i]: print('  ', np.round(cc[i], 3), round(float(ca[i] * 1e4), 2), 'cm2 agree', round(float(best[i]), 2))
