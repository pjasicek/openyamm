"""Rasterise a UV layer at N x N: per texel the rest-pose 3D position, the face normal, the dominant bone and whether
it is an eyeball (a loose piece). Body faces only for UVMap, head faces only for HeadUV.
Writes work/uvraster_<layer>.npz. Args: -- <blend> <layer> <N>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
blend, layer, N = sys.argv[sys.argv.index('--') + 1:]; N = int(N)
bpy.ops.wm.open_mainfile(filepath=C.path(blend))
rig = bpy.data.objects[C.RIG]
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
b = bpy.data.objects[C.MESH]; me = b.data
co = np.array([tuple(v.co) for v in me.vertices])
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
names = [g.name for g in b.vertex_groups]
dom = np.array([max(v.groups, key=lambda e: e.weight).group if len(v.groups) else -1 for v in me.vertices])
# loose pieces (eyeballs): vertex islands other than the largest
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
island = np.full(len(co), -1, np.int32); k = 0
for v in bm.verts:
    if island[v.index] >= 0:
        continue
    stack = [v]; island[v.index] = k
    while stack:
        a = stack.pop()
        for e in a.link_edges:
            o = e.other_vert(a)
            if island[o.index] < 0:
                island[o.index] = k; stack.append(o)
    k += 1
main = np.bincount(island).argmax()
uv = me.uv_layers[layer].data
pos = np.zeros((N, N, 3), np.float32); nrm = np.zeros((N, N, 3), np.float32)
bone = np.full((N, N), -1, np.int32); eye = np.zeros((N, N), bool); valid = np.zeros((N, N), bool)
want_head = layer == 'HeadUV'
me.calc_loop_triangles()
for t in me.loop_triangles:
    if bool(hd[t.polygon_index]) != want_head:
        continue
    L = list(t.loops); Vv = list(t.vertices)
    Pq = np.array([tuple(uv[l].uv) for l in L]) * N
    x0, y0 = np.floor(Pq.min(0)).astype(int); x1, y1 = np.ceil(Pq.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
    if x1 < x0 or y1 < y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, bb, c = Pq
    den = (bb[1] - c[1]) * (a[0] - c[0]) + (c[0] - bb[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    w0 = ((bb[1] - c[1]) * (xs - c[0]) + (c[0] - bb[0]) * (ys - c[1])) / den
    w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    w2 = 1 - w0 - w1
    m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
    if not m.any():
        continue
    iy = (N - 1 - (ys[m] - 0.5)).astype(int); ix = (xs[m] - 0.5).astype(int)   # image rows from the top
    p3 = w0[m, None] * co[Vv[0]] + w1[m, None] * co[Vv[1]] + w2[m, None] * co[Vv[2]]
    pos[iy, ix] = p3; nrm[iy, ix] = tuple(t.normal); valid[iy, ix] = True
    bone[iy, ix] = dom[Vv[0]]; eye[iy, ix] = island[Vv[0]] != main
np.savez_compressed(C.path(f'work/uvraster_{layer}.npz'), pos=pos, nrm=nrm, bone=bone, eye=eye, valid=valid,
                    bone_names=np.array(names))
print('RASTER', layer, 'texels', int(valid.sum()), 'eye', int(eye.sum()))
