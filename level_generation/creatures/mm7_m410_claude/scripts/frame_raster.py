"""Rasterise the body UV layer (UVMap) at N x N with the tangent frame per texel: the interpolated smooth vertex normal and
the per-triangle +u / +v surface directions, for smooth_skin_normals.py. Body faces only (head faces and props skipped,
as uv_raster.py). Writes work/frameraster_UVMap.npz (nrm, tu, tv). Args: -- <blend> <N>"""
import bpy, sys, os
import numpy as np
blend, N = sys.argv[sys.argv.index('--') + 1:]; N = int(N)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(v.co) for v in me.vertices]); vn = np.array([tuple(v.normal) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
uv = me.uv_layers['UVMap'].data
nrm = np.zeros((N, N, 3), np.float32); tu = np.zeros((N, N, 3), np.float32); tv = np.zeros((N, N, 3), np.float32)
me.calc_loop_triangles()
for t in me.loop_triangles:
    if hd[t.polygon_index] or pv[t.vertices[0]] >= 1000:
        continue
    L = list(t.loops); V = list(t.vertices)
    U = np.array([tuple(uv[l].uv) for l in L]); P = U * N; X = co[V]
    d1, d2 = U[1] - U[0], U[2] - U[0]; e1, e2 = X[1] - X[0], X[2] - X[0]
    det = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(det) < 1e-12:
        continue
    du = (e1 * d2[1] - e2 * d1[1]) / det; dv = (e2 * d1[0] - e1 * d2[0]) / det
    x0, y0 = np.floor(P.min(0)).astype(int); x1, y1 = np.ceil(P.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
    if x1 < x0 or y1 < y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, bb, c = P
    den = (bb[1] - c[1]) * (a[0] - c[0]) + (c[0] - bb[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    w0 = ((bb[1] - c[1]) * (xs - c[0]) + (c[0] - bb[0]) * (ys - c[1])) / den
    w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    w2 = 1 - w0 - w1
    m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
    iy = (N - 1 - (ys[m] - 0.5)).astype(int); ix = (xs[m] - 0.5).astype(int)
    n = w0[m, None] * vn[V[0]] + w1[m, None] * vn[V[1]] + w2[m, None] * vn[V[2]]
    nrm[iy, ix] = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    tu[iy, ix] = du; tv[iy, ix] = dv
np.savez_compressed(os.path.join(HERE, 'work', 'frameraster_UVMap.npz'), nrm=nrm, tu=tu, tv=tv)
print('FRAMERASTER', N, 'covered', round(float((np.abs(nrm).sum(2) > 0).mean()), 3))
