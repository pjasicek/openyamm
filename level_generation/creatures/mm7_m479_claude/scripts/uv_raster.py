"""Rasterise UVMap at N x N: per texel the piece id (-1 empty), part (0 bark, 1/2 teeth, 3 eyes), rest-pose 3D position
and normal, and the dominant bone. Writes work/uvraster_<tag>_<N>.npz. Args: -- <blend> <N> <tag>"""
import bpy, sys, os
import numpy as np
blend, N, tag = sys.argv[sys.argv.index('--') + 1:]; N = int(N)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(v.co) for v in me.vertices]); no = np.array([tuple(v.normal) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
pa = np.zeros(len(co), np.int32); me.attributes['part'].data.foreach_get('value', pa)
names = [g.name for g in b.vertex_groups]
dom = np.array([max(v.groups, key=lambda e: e.weight).group if len(v.groups) else -1 for v in me.vertices])
uv = me.uv_layers['UVMap'].data
piece = np.full((N, N), -1, np.int32); part = np.full((N, N), -1, np.int32)
pos = np.zeros((N, N, 3), np.float32); nrm = np.zeros((N, N, 3), np.float32); bone = np.full((N, N), -1, np.int32)
me.calc_loop_triangles()
for t in me.loop_triangles:
    L = list(t.loops); V = list(t.vertices)
    P = np.array([tuple(uv[l].uv) for l in L]) * N
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
    iy = (N - 1 - (ys[m] - 0.5)).astype(int); ix = (xs[m] - 0.5).astype(int)    # image rows top-down
    piece[iy, ix] = pv[V[0]]; part[iy, ix] = pa[V[0]]
    pos[iy, ix] = w0[m, None] * co[V[0]] + w1[m, None] * co[V[1]] + w2[m, None] * co[V[2]]
    nrm[iy, ix] = np.array(tuple(t.normal))
    bone[iy, ix] = dom[V[np.argmax([w0[m].mean(), w1[m].mean(), w2[m].mean()])]]
np.savez_compressed(os.path.join(HERE, 'work', f'uvraster_{tag}_{N}.npz'), piece=piece, part=part, pos=pos, nrm=nrm,
                    bone=bone, bone_names=np.array(names))
print('RASTER', tag, N, 'covered', round(float((piece >= 0).mean()), 3))
