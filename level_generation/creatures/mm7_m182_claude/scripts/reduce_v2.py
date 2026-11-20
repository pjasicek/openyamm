"""v2 reduction ladder, step 1 (Blender): decimate the symmetric unrigged body before rigging (the v2 weights are
rule-based, so they are computed on the reduced mesh), keep the procedural wings, crest spike tips and claws.

Decimate (collapse, X symmetry) with a protection group (wings, the outer quarter of every crest shell, fore and hind
claws), ratio 0.9^step of the body, then symmetrize from +X again so the result is exactly mirror-symmetric.
Usage: reduce_v2.py -- <static_v5.blend> <step> <out.blend>"""
import bpy, bmesh, json, sys
import numpy as np
from mathutils import Vector, kdtree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); step = int(a[1])
o = bpy.data.objects['Body']; me = o.data
co = np.array([v.co[:] for v in me.vertices]); pa = np.array([v.value for v in me.attributes['part'].data])
wk = np.array([v.value for v in me.attributes['wing_kind'].data]); x, y, z = co.T; ax = np.abs(x)
fixed = set(np.where(wk >= 0)[0].tolist())
fixed |= set(np.where((wk < 0) & (z < .03) & (y > -.12) & (y < .0))[0].tolist())                      # hind claws
fixed |= set(np.where((wk < 0) & (y < -.40) & (z < .20) & (ax > .02))[0].tolist())                     # fore claws
main = np.where((pa == 0) & (wk < 0))[0]; tree = kdtree.KDTree(len(main))
for i in main: tree.insert(Vector(co[i]), int(i))
tree.balance()
for part in sorted(set(pa) - {0}):
    ids = np.where(pa == part)[0]; dist = np.array([tree.find(Vector(co[i]))[2] for i in ids])
    fixed.update(int(i) for i in ids[dist >= np.quantile(dist, .75)])
body_tris = sum(len(f.vertices) - 2 for f in me.polygons if f.material_index != 2)
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
g = o.vertex_groups.new(name='Protect'); g.add(sorted(fixed), 1., 'REPLACE')
mod = o.modifiers.new('Reduce', 'DECIMATE'); mod.ratio = .9 ** step; mod.vertex_group = g.name; mod.invert_vertex_group = True
mod.vertex_group_factor = 1000.; mod.use_collapse_triangulate = True; mod.use_symmetry = True; mod.symmetry_axis = 'X'
bpy.ops.object.modifier_apply(modifier=mod.name)
if o.vertex_groups.get('Protect'): o.vertex_groups.remove(o.vertex_groups['Protect'])
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.symmetrize(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:], direction='X', dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-6: v.co.x = 0.
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-7)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(me); bm.free(); me.update()
co2 = np.array([v.co[:] for v in me.vertices]); kd = kdtree.KDTree(len(co2))
for i, p in enumerate(co2): kd.insert(Vector(p), i)
kd.balance(); worst = max(kd.find(Vector((-p[0], p[1], p[2])))[2] for p in co2)
rep = {'step': step, 'ratio': .9 ** step, 'body_triangles_before': body_tris,
       'body_triangles': sum(len(f.vertices) - 2 for f in me.polygons if f.material_index != 2),
       'wing_triangles': sum(len(f.vertices) - 2 for f in me.polygons if f.material_index == 2),
       'triangles': sum(len(f.vertices) - 2 for f in me.polygons), 'protected': len(fixed), 'mirror_max_m': worst}
json.dump(rep, open(a[2].replace('.blend', '.json'), 'w'), indent=2); print('REDUCE', rep)
bpy.ops.wm.save_as_mainfile(filepath=a[2])
