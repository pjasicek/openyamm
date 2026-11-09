"""Closed outer wrap of the assembled figure: triangles rasterised to voxels, closed by R voxels, exterior flood from the box, solid = not exterior, eroded back; blocky surface quads for Blender's remesh.
Heals Meshy's layered, torn shells (mane, lips, nostrils) and joins head and body into one closed skin. Args: <in npz> <out npz> [h] [R]"""
import sys
import numpy as np
from scipy import ndimage as ndi
IN, OUT = sys.argv[1:3]
h = float(sys.argv[3]) if len(sys.argv) > 3 else 0.004
R = int(sys.argv[4]) if len(sys.argv) > 4 else 2
Z = np.load(IN); co, tri, pa = Z['co'], Z['tri'], Z['part']
keep = np.isin(pa[tri[:, 0]], (0, 10, 15))          # eyes stay separate pieces
T = co[tri[keep]]
lo = co.min(0) - h * (R + 4); hi = co.max(0) + h * (R + 4)
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
print('OCC', occ.sum() / 1e6)
d = ndi.distance_transform_edt(~occ)
print('EDT1')
closed = d <= R
lab, n = ndi.label(~closed)
ext = lab == lab[0, 0, 0]
print('LABELS', n, 'exterior', ext.sum() / 1e6, 'of', closed.size / 1e6)
solid = ~ext
del lab, closed
d2 = ndi.distance_transform_edt(solid)
print('EDT2')
solid2 = d2 > R
lab, n = ndi.label(solid2); sz = ndi.sum(solid2, lab, range(1, n + 1)); print('SOLID parts', n, np.sort(sz)[-6:])
solid2 = lab == (1 + int(np.argmax(sz)))
# voxel-cornered quads between solid and empty
S = solid2
quads = []; 
for ax in range(3):
    a = np.diff(S.astype(np.int8), axis=ax)
    for sgn in (1, -1):
        idx = np.argwhere(a == sgn)
        u, v = [(1, 2), (2, 0), (0, 1)][ax]
        p = idx.copy(); p[:, ax] += 1
        c0 = p; c1 = p.copy(); c1[:, u] += 1; c2 = c1.copy(); c2[:, v] += 1; c3 = p.copy(); c3[:, v] += 1
        q = np.stack([c0, c1, c2, c3], 1) if sgn == -1 else np.stack([c0, c3, c2, c1], 1)
        quads.append(q)
Qd = np.concatenate(quads)
key = Qd[..., 0].astype(np.int64) * (dim[1] + 2) * (dim[2] + 2) + Qd[..., 1].astype(np.int64) * (dim[2] + 2) + Qd[..., 2].astype(np.int64)
u, inv = np.unique(key.ravel(), return_inverse=True)
V = np.c_[u // ((dim[1] + 2) * (dim[2] + 2)), (u // (dim[2] + 2)) % (dim[1] + 2), u % (dim[2] + 2)].astype(float) * h + lo
F = inv.reshape(-1, 4)
print('BLOCKS verts', len(V), 'quads', len(F))
np.savez(OUT, V=V, F=F, h=h)
