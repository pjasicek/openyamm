"""Join the rigged wings into the body for texturing and export: the 'Wings' object (wings_rig.py weights on
B_Spine2 / Wing_<s>_1..3) is reduced first (collapse decimation keeps the vertex groups; WING_TRIS), given the body's
point attributes (piece = its Smart Topology part, garment 5 = wing, orig_co) and joined into 'Body' under the same
armature. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
WING_TRIS = int(os.environ.get('WING_TRIS', '2200'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; wings = bpy.data.objects['Wings']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
tris = sum(len(p.vertices) - 2 for p in wings.data.polygons)
for o in bpy.data.objects:
    o.select_set(o == wings)
bpy.context.view_layer.objects.active = wings
if tris > WING_TRIS:
    m = wings.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = WING_TRIS / tris
    bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
    bpy.ops.object.modifier_apply(modifier='dec')
after = sum(len(p.vertices) - 2 for p in wings.data.polygons)
wm = wings.data
wm.attributes.new('garment', 'INT', 'POINT').data.foreach_set('value', [5] * len(wm.vertices))
for o in bpy.data.objects:
    o.select_set(o in (body, wings))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
me = body.data
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
print('WINGJOIN wings', tris, '->', after, 'tris; body total', sum(len(p.vertices) - 2 for p in me.polygons),
      'wing vertices', int((gv == 5).sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
