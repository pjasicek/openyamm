"""Add the Treant's eyes as their own geometry and bones (the native resting frame m479sa0 shows NO face: the eyes open
only when it attacks or is hit). work/rig_v1u.blend -> work/rig_v2.blend.
Smart Topology modelled no eyes (Meshy only painted them). Per eye: an almond (flattened ellipsoid, 0.19 x 0.11 m,
0.06 deep) on its own bone Eye_L / Eye_R (parent Trunk2), set into the bark at the eye position measured on the front HD master
(references_hd/01_front.png green pixels: z 1.80 m, x +-0.20 m; ray cast onto the trunk front along +Y), facing the surface normal blended with -Y. The bone head sits 4 cm inside the bark, so
scaling it to 0.05 sinks the eye out of sight (Standing) and 1 opens it.
UVs: both eyes share one free square of the atlas (found from the existing islands at 512 px), planar from the front;
compose_m479.py paints it (green iris, slit pupil, dark rim). 'part' = 3 for the eyes, 'piece' 300/301.
Args: -- <x_left> <z_left> <x_right> <z_right>   (eye centres in metres; left = character's left = +X)"""
import bpy, bmesh, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
xl, zl, xr, zr = map(float, sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1u.blend'))
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = body.data
W_EYE, H_EYE, D_EYE, SINK = 0.19, 0.11, 0.06, 0.026
# ---------------------------------------------------------------- free UV square
N = 512
occ = np.zeros((N, N), bool)
uv = me.uv_layers['UVMap'].data
me.calc_loop_triangles()
for t in me.loop_triangles:
    P = np.array([tuple(uv[l].uv) for l in t.loops]) * N
    x0, y0 = np.floor(P.min(0)).astype(int) - 2; x1, y1 = np.ceil(P.max(0)).astype(int) + 2
    occ[max(y0, 0):min(y1, N), max(x0, 0):min(x1, N)] = True          # bbox occupancy (conservative)
S = 24                                                                 # square side in 512-px units (~0.047 UV)
free = None
try:
    from scipy import ndimage
    dist = ndimage.distance_transform_cdt(~occ, metric='chessboard')
    yy, xx = np.unravel_index(np.argmax(dist), dist.shape)
    if dist[yy, xx] >= S // 2 + 1:
        free = (xx - S // 2, yy - S // 2)
except Exception:
    pass
if free is None:
    for yy in range(0, N - S):
        for xx in range(0, N - S):
            if not occ[yy:yy + S, xx:xx + S].any():
                free = (xx, yy); break
        if free:
            break
u0, v0 = free[0] / N, free[1] / N; side = S / N
print('EYES uv square', round(u0, 4), round(v0, 4), round(side, 4))
# ---------------------------------------------------------------- place
bm0 = bmesh.new(); bm0.from_mesh(me); bvh = BVHTree.FromBMesh(bm0)
eyes = []
for name, x, z in (('Eye_L', xl, zl), ('Eye_R', xr, zr)):
    hit, nrm, _, _ = bvh.ray_cast(Vector((x, -3.0, z)), Vector((0, 1, 0)))
    nrm = (nrm.normalized() + Vector((0, -1.5, 0))).normalized()
    eyes.append((name, hit, nrm))
    print('EYES', name, [round(c, 3) for c in hit], [round(c, 2) for c in nrm])
bm0.free()
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.int.get('piece'); part = bm.verts.layers.int.get('part'); uvl = bm.loops.layers.uv['UVMap']
oco = bm.verts.layers.float_vector.get('orig_co')
for k, (name, hit, nrm) in enumerate(eyes):
    fwd = -nrm                                                          # eye looks along nrm (out of the bark)
    up = Vector((0, 0, 1)); side_ax = up.cross(nrm).normalized(); up = nrm.cross(side_ax).normalized()
    centre = hit - nrm * (D_EYE / 2 - SINK)
    res = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0)
    vs = res['verts']
    R = Matrix((side_ax, up, nrm)).transposed()
    for v in vs:
        l = v.co.copy()
        v.co = centre + R @ Vector((l.x * W_EYE / 2, l.y * H_EYE / 2 * (1 - 0.35 * l.x * l.x), l.z * D_EYE / 2))
        v[lay] = 300 + k; v[part] = 3
        if oco is not None:
            v[oco] = v.co
    fs = {f for v in vs for f in v.link_faces}
    for f in fs:
        for lp in f.loops:
            d = R.transposed() @ (lp.vert.co - centre)
            mir = -1 if k == 1 else 1
            uu = 0.5 + 0.5 * mir * d.x / (W_EYE / 2) * 0.9; vv = 0.5 + 0.5 * d.y / (H_EYE / 2) * 0.9
            lp[uvl].uv = (u0 + side * min(max(uu, 0.02), 0.98), v0 + side * min(max(vv, 0.02), 0.98))
bm.to_mesh(me); bm.free(); me.update()
for poly in me.polygons:                       # organic strands: smooth shading everywhere (Meshy returned flat faces)
    poly.use_smooth = True
co = np.array([tuple(v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for k, (name, hit, nrm) in enumerate(eyes):
    b = rig.data.edit_bones.new(name); b.head = hit - nrm * 0.04; b.tail = hit + nrm * 0.06
    b.align_roll(Vector((0, 0, 1))); b.parent = rig.data.edit_bones['Trunk2']
bpy.ops.object.mode_set(mode='OBJECT')
for k, (name, hit, nrm) in enumerate(eyes):
    g = body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
    idx = [int(i) for i in np.nonzero(pv == 300 + k)[0]]
    for gg in body.vertex_groups:
        gg.remove(idx)
    g.add(idx, 1.0, 'REPLACE')
json.dump({'uv_square': [u0, v0, side], 'eyes': {n: {'centre': list(h), 'normal': list(nn)} for n, h, nn in eyes}},
          open(os.path.join(HERE, 'work', 'eyes.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v2.blend'))
print('EYES saved', len(co), 'verts')
