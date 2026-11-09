"""Texel raster of the body faces in the body square (atlas u / (1024/2080), v) at 1024: per texel the 3D rest
position, face normal and the dominant bone of the face. Out: work/body_raster.npz."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 1024; BODY_W = 1024 / 2080
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'uv_master.blend'))
o = bpy.data.objects['Body']; me = o.data; uv = me.uv_layers.active.data
co = np.array([v.co[:] for v in me.vertices])
names = [g.name for g in o.vertex_groups]
dom = np.array([max(v.groups, key=lambda e: e.weight).group if len(v.groups) else -1 for v in me.vertices])
bone = np.full((N, N), -1, np.int32); pos = np.zeros((N, N, 3), np.float32); nrm = np.zeros((N, N, 3), np.float32)
me.calc_loop_triangles()
for t in me.loop_triangles:
    U = np.array([tuple(uv[l].uv) for l in t.loops])
    if U[:, 0].mean() >= .5:
        continue
    P = U * [N / BODY_W, N]
    x0, y0 = np.floor(P.min(0)).astype(int); x1, y1 = np.ceil(P.max(0)).astype(int)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, N - 1), min(y1, N - 1)
    if x1 < x0 or y1 < y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    a, b, c = P
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    w2 = 1 - w0 - w1; m = (w0 >= -.02) & (w1 >= -.02) & (w2 >= -.02)
    if not m.any():
        continue
    iy = (N - 1 - (ys[m] - .5)).astype(int); ix = (xs[m] - .5).astype(int); V = list(t.vertices)
    pos[iy, ix] = w0[m, None] * co[V[0]] + w1[m, None] * co[V[1]] + w2[m, None] * co[V[2]]
    nrm[iy, ix] = me.polygons[t.polygon_index].normal[:]
    bone[iy, ix] = dom[V[0]]
np.savez_compressed(os.path.join(HERE, 'work', 'body_raster.npz'), bone=bone, pos=pos, normal=nrm, bone_names=np.array(names))
print('RASTER covered', round(float((bone >= 0).mean()), 3))
