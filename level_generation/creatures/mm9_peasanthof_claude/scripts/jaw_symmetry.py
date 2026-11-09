#!/usr/bin/env python3
"""Mirror asymmetry of the head skin shell over the jaw, cheeks and chin (user review r7, 2026-11-04: "deformed right part of the
face/chin? not symmetrical?"). Bind positions of the head material's skin shell (the connected part holding the nose tip) in a GLB; every vertex in
the band YLO < y < YHI (m) is mirrored in x and matched to the nearest shell vertex; the distance is the asymmetry. The mirror plane is
the x of the nose tip (the most forward shell vertex 1.70-1.78 m). Prints max / p95 / p50 (mm) overall and per side, and the 5 worst vertices.
Point-to-surface (r10): the mirrored vertex is also matched to the closest point on the shell's triangles (exact, 24 nearest
triangles by centroid), which is the asymmetry free of the tessellation; printed as JAWSYM-SURF.
Args: <glb> [ylo 1.62] [yhi 1.76] [material PeasantHOFHead] [zmin: front of this z only]"""
import sys
import numpy as np
from pygltflib import GLTF2
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
glb = sys.argv[1]; ylo = float(sys.argv[2]) if len(sys.argv) > 2 else 1.62; yhi = float(sys.argv[3]) if len(sys.argv) > 3 else 1.76
mat = sys.argv[4] if len(sys.argv) > 4 else 'PeasantHOFHead'
g = GLTF2().load(glb); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name == mat)
P = acc(prim.attributes.POSITION).astype(float); T = acc(prim.indices).reshape(-1, 3)
_, inv = np.unique(np.round(P, 5), axis=0, return_inverse=True); inv = inv.ravel()
e = inv[np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]]; n = inv.max() + 1
nc, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
U = np.zeros((n, 3)); U[inv] = P
fr = np.where((U[:, 1] > 1.66) & (U[:, 1] < 1.80))[0]; big = lab[fr[np.argmax(U[fr, 2])]]   # the component holding the nose tip
S = U[lab == big]
zmin = float(sys.argv[5]) if len(sys.argv) > 5 else -9.0
B = S[(S[:, 1] > ylo) & (S[:, 1] < yhi) & (S[:, 2] > zmin)]
F = S[(S[:, 1] > 1.70) & (S[:, 1] < 1.78)]; cx = F[np.argmax(F[:, 2]), 0]    # mirror plane through the nose tip
M = B.copy(); M[:, 0] = 2 * cx - M[:, 0]
d, _ = cKDTree(S).query(M)
d *= 1000
def closest_tri(Q, A, B, C):
    """Closest points on triangles (A,B,C) to Q, all (n,3); Ericson's region test, vectorised."""
    ab, ac, ap = B - A, C - A, Q - A
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = Q - B; d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = Q - C; d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-18, 1e-18, va + vb + vc)
    v, w = vb / den, vc / den
    R = A + ab * v[:, None] + ac * w[:, None]
    def sel(m, X):
        R[m] = X[m]
    sel((d1 <= 0) & (d2 <= 0), A)
    sel((d3 >= 0) & (d4 <= d3), B)
    sel((d6 >= 0) & (d5 <= d6), C)
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); t = d1 / np.where(d1 - d3 == 0, 1e-18, d1 - d3); X = A + ab * t[:, None]; sel(m & ~((d1 <= 0) & (d2 <= 0)) & ~((d3 >= 0) & (d4 <= d3)), X)
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); t = d2 / np.where(d2 - d6 == 0, 1e-18, d2 - d6); X = A + ac * t[:, None]; sel(m & ~((d1 <= 0) & (d2 <= 0)) & ~((d6 >= 0) & (d5 <= d6)), X)
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0); t = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-18, (d4 - d3) + (d5 - d6))
    X = B + (C - B) * t[:, None]; sel(m & ~((d3 >= 0) & (d4 <= d3)) & ~((d6 >= 0) & (d5 <= d6)), X)
    return R
TS = T[lab[inv[T[:, 0]]] == big]
TA, TB, TC = P[TS[:, 0]], P[TS[:, 1]], P[TS[:, 2]]
_, cand = cKDTree((TA + TB + TC) / 3).query(M, k=24)
ds = np.full(len(M), 9.0)
for k in range(cand.shape[1]):
    j = cand[:, k]; R = closest_tri(M, TA[j], TB[j], TC[j]); ds = np.minimum(ds, np.linalg.norm(R - M, axis=1))
ds *= 1000
print(f'JAWSYM-SURF {glb.split("/")[-1]} band {ylo}-{yhi}: max {ds.max():.1f} p95 {np.percentile(ds,95):.1f} p50 {np.median(ds):.1f} mm;'
      f' x<c p95 {np.percentile(ds[B[:,0]<cx],95):.1f}, x>c p95 {np.percentile(ds[B[:,0]>cx],95):.1f}')
for i in np.argsort(-ds)[:5]: print('   worst-surf', np.round(B[i], 3), round(float(ds[i]), 1), 'mm')
print(f'JAWSYM {glb.split("/")[-1]} band {ylo}-{yhi} m, {len(B)} verts, centre x {cx*1000:.1f} mm: max {d.max():.1f} p95 {np.percentile(d,95):.1f} p50 {np.median(d):.1f} mm;'
      f' x<c max {d[B[:,0]<cx].max():.1f}, x>c max {d[B[:,0]>cx].max():.1f}')
for i in np.argsort(-d)[:5]: print('   worst', np.round(B[i], 3), round(float(d[i]), 1), 'mm')
# silhouette per side: half-width of the shell (max |x - c|) on each side per 1 cm slice, front part (z > zmin)
print('   half-widths (mm) per slice: y, left (x<c), right (x>c), diff')
for y0 in np.arange(ylo, yhi, 0.01):
    sl = S[(S[:, 1] >= y0) & (S[:, 1] < y0 + 0.01) & (S[:, 2] > zmin)]
    if len(sl) < 4: continue
    l = cx - sl[:, 0].min(); r = sl[:, 0].max() - cx
    print(f'   {y0:.2f}  {l*1000:6.1f} {r*1000:6.1f} {abs(l-r)*1000:6.1f}')
