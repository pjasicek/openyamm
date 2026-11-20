"""Join the rigged wings and tail back into the gargoyle's body for texturing and export. The wings are reduced first
(collapse decimation keeps the vertex groups; WING_TRIS) with the seam vertices (within 1 mm of a body vertex: the split
edges of split_parts.py) protected so they still meet the body; both get garment 5 (wing) / 6 (tail). After the join the
seam's duplicated vertices are merged (1 mm), restoring one connected shell. Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
WING_TRIS = int(os.environ.get('WING_TRIS', '2600'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
bc = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
kd = KDTree(len(bc))
for i, c in enumerate(bc):
    kd.insert(c, i)
kd.balance()
report = {}
for name, garment, target in (('Wings', 5, WING_TRIS), ('Tail', 6, 10 ** 9)):
    ob = bpy.data.objects[name]; me = ob.data
    co = np.array([tuple(ob.matrix_world @ v.co) for v in me.vertices])
    seam = [i for i, c in enumerate(co) if kd.find(c)[2] < 0.001]
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    if tris > target:
        vg = ob.vertex_groups.new(name='_seam'); vg.add(seam, 1.0, 'REPLACE')
        m = ob.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = target / tris
        m.vertex_group = '_seam'; m.invert_vertex_group = True
        bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
        bpy.ops.object.modifier_apply(modifier='dec')
        ob.vertex_groups.remove(ob.vertex_groups['_seam'])
    me = ob.data
    a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
    a.data.foreach_set('value', [garment] * len(me.vertices))
    report[name] = (tris, sum(len(p.vertices) - 2 for p in me.polygons), len(seam))
for o in bpy.data.objects:
    o.select_set(o.name in ('Body', 'Wings', 'Tail'))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
me = body.data
bm = bmesh.new(); bm.from_mesh(me)
bnd = [v for v in bm.verts if v.is_boundary]
before = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bnd, dist=0.001)
bm.to_mesh(me); bm.free()
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
print('JOIN', {k: f'{a}->{b} tris, seam {c}' for k, (a, b, c) in report.items()}, 'merged', before - len(me.vertices),
      'vertices; body total', sum(len(p.vertices) - 2 for p in me.polygons), 'tris')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
