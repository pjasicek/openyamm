"""Clean skin: parts 0 and 10 closed and voxel-remeshed (Meshy's specks, folds and the neck zip go), the hands and forearm ends kept from the fitted mesh for sharp claws.
Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
VOX = 0.0036; XCUT = 0.70
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa)
P = np.array([v.co[:] for v in me.vertices])
kd = KDTree(len(P)); 
sk = np.nonzero(np.isin(pa, (0, 10)))[0]
kd = KDTree(len(sk))
for i in sk: kd.insert(P[i], int(i))
kd.balance()
skin = body.copy(); skin.data = me.copy(); skin.name = 'Skin'; bpy.context.scene.collection.objects.link(skin)
bm = bmesh.new(); bm.from_mesh(skin.data); lay = bm.verts.layers.int['part']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] not in (0, 10)], context='VERTS')
r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=80)
print('SKIN holes', len(r['faces']), 'boundary left', sum(1 for e in bm.edges if e.is_boundary), 'nonman', sum(1 for e in bm.edges if len(e.link_faces) > 2))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(skin.data); bm.free()
vx = skin.copy(); vx.data = skin.data.copy(); vx.name = 'Vox'; bpy.context.scene.collection.objects.link(vx)
bpy.context.view_layer.objects.active = vx
for o in bpy.data.objects: o.select_set(o is vx)
m = vx.modifiers.new('r', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = VOX; m.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='r')
print('VOX', len(vx.data.vertices), len(vx.data.polygons))
bm = bmesh.new(); bm.from_mesh(vx.data)
# largest component only
seen = set(); comps = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cc = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y); cc.append(y)
    comps.append(cc)
comps.sort(key=len, reverse=True)
print('VOX comps', [len(c) for c in comps[:6]])
for c in comps[1:]: bmesh.ops.delete(bm, geom=c, context='VERTS')
for sgn in (1, -1):
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(sgn * XCUT, 0, 0), plane_no=(sgn, 0, 0), clear_outer=True)
# belt centre: Meshy's folds round the plate
for _ in range(12):
    mv = {}
    for v in bm.verts:
        if abs(v.co.x) < 0.16 and 0.17 < v.co.z < 0.40 and v.co.y < 0:
            w = min(1.0, (0.16 - abs(v.co.x)) / 0.03) * min(1.0, (v.co.z - 0.17) / 0.03) * min(1.0, (0.40 - v.co.z) / 0.03)
            mv[v] = (sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges), w)
    for v, (c, w) in mv.items(): v.co = v.co * (1 - w * 0.7) + c * w * 0.7
bv_ = {}
for sgn in (1, -1):
    bv_[sgn] = [e for e in bm.edges if e.is_boundary and sgn * e.verts[0].co.x > 0.6]
bm.to_mesh(vx.data); bm.free()
# the kept arm ends
ke = body.copy(); ke.data = skin.data.copy(); ke.name = 'Ends'; bpy.context.scene.collection.objects.link(ke)
bm = bmesh.new(); bm.from_mesh(ke.data)
for sgn in (1, -1):
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(sgn * XCUT, 0, 0), plane_no=(sgn, 0, 0), clear_inner=False, clear_outer=False)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if abs(v.co.x) < XCUT - 1e-4], context='VERTS')
bm.to_mesh(ke.data); bm.free()
# join: voxel, ends; each end's ring vertices weld onto the voxel ring
bm = bmesh.new(); bm.from_mesh(vx.data); lay2 = bm.verts.layers.int.get('part') or bm.verts.layers.int.new('part')
mark = bm.verts.layers.int.new('mk')
for v in bm.verts: v[mark] = 1
bm.from_mesh(ke.data)
bm.verts.ensure_lookup_table()
tm = {}
for sgn in (1, -1):
    a = [v for v in bm.verts if v[mark] and v.is_boundary and abs(sgn * v.co.x - XCUT) < 1e-3]
    b = [v for v in bm.verts if not v[mark] and v.is_boundary and abs(sgn * v.co.x - XCUT) < 1e-3]
    print('RINGS', sgn, len(a), len(b))
    # move the end ring onto nearest voxel ring verts, drop surplus by welding the voxel ring onto it
    for u in a:
        tm[u] = min(b, key=lambda q: (q.co - u.co).length_squared)
bmesh.ops.weld_verts(bm, targetmap=tm)
bm.verts.layers.int.remove(mark)
bm.to_mesh(vx.data); bm.free()
Q = np.array([v.co[:] for v in vx.data.vertices])
part = np.array([pa[kd.find(q)[1]] for q in Q])
if 'part' not in vx.data.attributes: vx.data.attributes.new('part', 'INT', 'POINT')
vx.data.attributes['part'].data.foreach_set('value', part.tolist())
# put the rest back
bm = bmesh.new(); bm.from_mesh(me); lay = bm.verts.layers.int['part']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] in (0, 10)], context='VERTS')
bm.to_mesh(me); bm.free()
bpy.data.objects.remove(skin); bpy.data.objects.remove(ke)
for o in bpy.data.objects: o.select_set(o in (body, vx))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
for p in body.data.polygons: p.use_smooth = True
pa2 = np.zeros(len(body.data.vertices), int); body.data.attributes['part'].data.foreach_get('value', pa2)
print('FINAL', len(body.data.vertices), len(body.data.polygons), {int(k): int((pa2 == k).sum()) for k in np.unique(pa2)})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
