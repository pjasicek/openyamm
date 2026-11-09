#!/usr/bin/env python3
"""Head-only voxel closure for the giant (after mm9_bigfoot_claude/wrap_bf.py). The Meshy head carries its hair and beard as open
sheets over the skull, so a uniform closing either leaves them paper thin or, with a big radius, fills the face's own creases.
Here: closing by R voxels everywhere, and by RB voxels only behind the side rims of the hair (normalised y > YB), where the hair
hangs away from the skull and neck; the gap there becomes one solid hair mass, as MM9's. The front of the face keeps its detail.
Also writes the face npz for head_close.py (figure space). Args: <face raw npz> <eyes raw npz> <out blocks npz> <out face npz>
Placement: S, OY, OZ (chin, nose tip and crown matched to the fitted body)."""
import sys
import numpy as np
from scipy import ndimage as ndi
FACE, EYES, OUT, FOUT = sys.argv[1:5]
S, OY, OZ = 0.445, -0.044, 1.0546
h, R, RB, YB = 0.002, 2, 12, 0.03
F = np.load(FACE); E = np.load(EYES)
co = F['V'] * S + [0, OY, OZ]; tri = F['T']
ce = E['V'] * S + [0, OY, OZ]; te = E['T']
np.savez(FOUT, co=np.vstack([co, ce]), tri=np.vstack([tri, te + len(co)]), part=np.r_[np.full(len(co), 10), np.full(len(ce), 13)])
T = co[tri]
lo = co.min(0) - h * (RB + 4); hi = co.max(0) + h * (RB + 4)
dim = np.ceil((hi - lo) / h).astype(int) + 1
print('GRID', dim, dim.prod() / 1e6, 'M tris', len(T))
occ = np.zeros(dim, bool)
e = np.maximum(np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.maximum(np.linalg.norm(T[:, 2] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1)))
ns = np.ceil(e / (h * 0.5)).astype(int) + 1
for n in np.unique(ns):
    g = np.mgrid[0:n + 1, 0:n + 1].reshape(2, -1).T; g = g[g.sum(1) <= n] / n
    w = np.c_[g, 1 - g.sum(1)]
    Q = np.einsum('ij,ajk->aik', w, T[ns == n])
    I = ((Q.reshape(-1, 3) - lo) / h).astype(int)
    occ[I[:, 0], I[:, 1], I[:, 2]] = True
d = ndi.distance_transform_edt(~occ)
gy = (lo[1] + np.arange(dim[1]) * h - OY) / S      # normalised y per voxel row
gz = (lo[2] + np.arange(dim[2]) * h - OZ) / S
back = (gy[None, :, None] > YB) & (gz[None, None, :] < 0.42)
def solid_of(rad, region=None):
    closed = d <= rad
    lab, n = ndi.label(~closed)
    ext = lab == lab[0, 0, 0]
    sol = ~ext
    d2 = ndi.distance_transform_edt(sol)
    sol = d2 > rad
    return sol
small = solid_of(R)
big = solid_of(RB)
solid = small | (big & np.broadcast_to(back, dim))
print('SOLID small', small.sum() / 1e6, 'big', big.sum() / 1e6, 'added', (solid & ~small).sum() / 1e6)
lab, n = ndi.label(solid); sz = ndi.sum(solid, lab, range(1, n + 1)); print('SOLID parts', n, np.sort(sz)[-4:])
solid = lab == (1 + int(np.argmax(sz)))
quads = []
for ax in range(3):
    a = np.diff(solid.astype(np.int8), axis=ax)
    for sgn in (1, -1):
        idx = np.argwhere(a == sgn)
        u, v = [(1, 2), (2, 0), (0, 1)][ax]
        p = idx.copy(); p[:, ax] += 1
        c0 = p; c1 = p.copy(); c1[:, u] += 1; c2 = c1.copy(); c2[:, v] += 1; c3 = p.copy(); c3[:, v] += 1
        quads.append(np.stack([c0, c1, c2, c3], 1) if sgn == -1 else np.stack([c0, c3, c2, c1], 1))
Qd = np.concatenate(quads)
key = Qd[..., 0].astype(np.int64) * (dim[1] + 2) * (dim[2] + 2) + Qd[..., 1].astype(np.int64) * (dim[2] + 2) + Qd[..., 2].astype(np.int64)
u, inv = np.unique(key.ravel(), return_inverse=True)
V = np.c_[u // ((dim[1] + 2) * (dim[2] + 2)), (u // (dim[2] + 2)) % (dim[1] + 2), u % (dim[2] + 2)].astype(float) * h + lo
print('BLOCKS verts', len(V), 'quads', len(inv) // 4)
np.savez(OUT, V=V, F=inv.reshape(-1, 4), h=h)
