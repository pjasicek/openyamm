#!/usr/bin/env python3
"""Solid occupancy of the Meshy return's main body, robust to its inner layer and the holes where the layers meet.

The Smart Topology return is a skin with a second layer 0.5-6 mm under it; the layers join at a few places and the
cow's front legs hang on the inner layer only. Blender's voxel remesh turns that into a hollow slab (inner bubbles,
collapse decimation stalls with spikes). Here: every triangle of the main component is rasterised into a grid
(VOX), walls dilated by DILATE voxels (closes the junction holes), the outside flood-filled from the border;
inside = everything not reached. The boundary between inside and outside voxels is written as a closed quad mesh
(OBJ) for finish_solid.py (Blender: voxel remesh, smooth, shrink back onto the skin).
Args: <meshy glb> <out obj> [vox] [dilate]   (python with numpy, scipy and pygltflib)"""
import sys
import numpy as np
from scipy import ndimage
from pygltflib import GLTF2

src, out = sys.argv[1], sys.argv[2]
VOX = float(sys.argv[3]) if len(sys.argv) > 3 else 0.002
DIL = int(sys.argv[4]) if len(sys.argv) > 4 else 1
g = GLTF2().load(src)
blob = g.binary_blob()


def acc(i, comps, dt):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    o = bv.byteOffset + (a.byteOffset or 0)
    n = a.count * comps
    arr = np.frombuffer(blob[o:o + n * np.dtype(dt).itemsize], dtype=dt)
    return arr.reshape(-1, comps) if comps > 1 else arr


ctype = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32}
P = acc(g.meshes[0].primitives[0].attributes.POSITION, 3, np.float32).astype(np.float64)
ia = g.meshes[0].primitives[0].indices
I = acc(ia, 1, ctype[g.accessors[ia].componentType]).reshape(-1, 3)
# weld and take the largest connected component
key = np.round(P / 1e-5).astype(np.int64)
_, inv = np.unique(key, axis=0, return_inverse=True)
inv = inv.ravel()
T = inv[I]
nv = inv.max() + 1
import scipy.sparse as sp
e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv))
ncomp, lab = sp.csgraph.connected_components(A, directed=False)
big = np.bincount(lab).argmax()
Pw = np.zeros((nv, 3)); Pw[inv] = P
T = T[lab[T[:, 0]] == big]
lo = Pw[np.unique(T)].min(0) - 4 * VOX
hi = Pw[np.unique(T)].max(0) + 4 * VOX
shape = np.ceil((hi - lo) / VOX).astype(int) + 1
grid = np.zeros(shape, bool)
# rasterise: sample each triangle with spacing VOX / 2
a, b, c = Pw[T[:, 0]], Pw[T[:, 1]], Pw[T[:, 2]]
ext = np.maximum(np.linalg.norm(b - a, axis=1), np.linalg.norm(c - a, axis=1))
for k in np.unique(np.ceil(ext / (VOX * 0.5)).astype(int)):
    sel = np.ceil(ext / (VOX * 0.5)).astype(int) == k
    k = max(1, k)
    u, v = np.meshgrid(np.arange(k + 1), np.arange(k + 1))
    m = (u + v) <= k
    u, v = u[m] / k, v[m] / k
    pts = a[sel][:, None, :] + u[None, :, None] * (b - a)[sel][:, None, :] + v[None, :, None] * (c - a)[sel][:, None, :]
    idx = np.floor((pts.reshape(-1, 3) - lo) / VOX).astype(int)
    grid[idx[:, 0], idx[:, 1], idx[:, 2]] = True
wall = ndimage.binary_dilation(grid, iterations=DIL) if DIL > 0 else grid
lab2, n2 = ndimage.label(~wall)
border = set(np.unique(np.concatenate([lab2[0].ravel(), lab2[-1].ravel(), lab2[:, 0].ravel(), lab2[:, -1].ravel(),
                                       lab2[:, :, 0].ravel(), lab2[:, :, -1].ravel()])))
outside = np.isin(lab2, list(border - {0}))
inside = ~outside
# keep the largest inside component
lab3, n3 = ndimage.label(inside)
inside = lab3 == np.bincount(lab3.ravel())[1:].argmax() + 1
print('GRID shape', shape.tolist(), 'vox', VOX, 'dilate', DIL, 'inside voxels', int(inside.sum()),
      'outside regions', len(border - {0}), 'inner cavities filled', n2 - len(border - {0}))
# boundary quads between inside and outside voxels
verts = {}
faces = []


def vid(ijk):
    if ijk not in verts:
        verts[ijk] = len(verts)
    return verts[ijk]


pad = np.pad(inside, 1)
for axis in range(3):
    for sgn in (1, -1):
        nb = np.roll(pad, -sgn, axis=axis)
        faces_ijk = np.argwhere(pad & ~nb) - 1
        for ijk in faces_ijk:
            i, j, k = ijk
            # face on the +axis (sgn 1) or -axis side of voxel ijk
            o = [i, j, k]; o[axis] += 1 if sgn > 0 else 0
            ax1, ax2 = [x for x in range(3) if x != axis]
            q = []
            for d1, d2 in ((0, 0), (1, 0), (1, 1), (0, 1)):
                p = list(o); p[ax1] += d1; p[ax2] += d2
                q.append(vid(tuple(p)))
            # outward winding: normal along +axis*sgn
            if (sgn > 0) != ((ax1, ax2, axis) in ((0, 1, 2), (1, 2, 0), (2, 0, 1))):
                q = q[::-1]
            faces.append(q)
V = np.zeros((len(verts), 3))
for ijk, i in verts.items():
    V[i] = lo + np.array(ijk) * VOX
with open(out, 'w') as f:
    f.write('# solid_grid.py\n')
    for p in V:
        f.write('v %.6f %.6f %.6f\n' % tuple(p))
    for q in faces:
        f.write('f %d %d %d %d\n' % tuple(x + 1 for x in q))
print('GRID faces', len(faces), 'verts', len(V))
