"""Rasterise a UV layer at N x N (or W x H: N given as e.g. 2048x1024, the packed body page): per texel the piece id (-1 empty), the rest-pose 3D position and the dominant bone.
Writes work/uvraster_<layer>.npz (piece, pos, bone, bone_names). Body faces only for UVMap, head faces only for HeadUV.
Args: -- <blend> <layer> <N>"""
import bpy, sys, os
import numpy as np
blend, layer, N = sys.argv[sys.argv.index('--') + 1:]
NW, NH = (int(v) for v in N.split('x')) if 'x' in N else (int(N), int(N))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gv = np.zeros(len(co), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
names = [g.name for g in b.vertex_groups]
dom = np.array([max(v.groups, key=lambda e: e.weight).group if len(v.groups) else -1 for v in me.vertices])
uv = me.uv_layers[layer].data
piece = np.full((NH, NW), -1, np.int32); garment = np.full((NH, NW), -1, np.int32); pos = np.zeros((NH, NW, 3), np.float32); bone = np.full((NH, NW), -1, np.int32)
want_head = layer == 'HeadUV'
me.calc_loop_triangles()
for t in me.loop_triangles:
    if bool(hd[t.polygon_index]) != want_head:
        continue
    L = list(t.loops); V = list(t.vertices)
    P = np.array([tuple(uv[l].uv) for l in L]) * np.array([NW, NH])
    x0, y0 = np.floor(P.min(0)).astype(int); x1, y1 = np.ceil(P.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, NW - 1), min(y1, NH - 1)
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
    iy = (NH - 1 - (ys[m] - 0.5)).astype(int); ix = (xs[m] - 0.5).astype(int)    # image rows top-down
    piece[iy, ix] = pv[V[0]]; garment[iy, ix] = gv[V[0]]
    pos[iy, ix] = (w0[m, None] * co[V[0]] + w1[m, None] * co[V[1]] + w2[m, None] * co[V[2]])
    bone[iy, ix] = dom[V[np.argmax([w0[m].mean(), w1[m].mean(), w2[m].mean()])]]
np.savez_compressed(os.path.join(HERE, 'work', f'uvraster_{layer}.npz'), piece=piece, garment=garment, pos=pos, bone=bone,
                    bone_names=np.array(names))
print('RASTER', layer, N, 'covered', round(float((piece >= 0).mean()), 3), 'pieces', sorted(set(np.unique(piece)) - {-1}))
