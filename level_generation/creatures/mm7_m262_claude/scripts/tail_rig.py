"""Tail bone for m262: the tail feather cards (garment 7, rigid on B_Pelvis by weights_fix.py) get their own bone
'B_Tail' (child of B_Pelvis; head where the cards meet the hips, tail toward the card tips) and are rigid on it, so the
flight can sway the tail and the death can fold it up against the floor (lying on her back, the pelvis-rigid tail
pointed into the floor and propped the corpse 0.47 m up). Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
tail = np.where(gv == 7)[0]; T = co[tail]
pel = np.array(rig.data.bones['B_Pelvis'].head_local)
d = np.linalg.norm(T - pel, axis=1)
root = T[d < np.percentile(d, 15)].mean(0); tip = T[d > np.percentile(d, 85)].mean(0)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.new('B_Tail'); eb.head = Vector(root); eb.tail = Vector(tip)
eb.parent = rig.data.edit_bones['B_Pelvis']; eb.align_roll(Vector((1, 0, 0)))
bpy.ops.object.mode_set(mode='OBJECT')
vg = body.vertex_groups.get('B_Tail') or body.vertex_groups.new(name='B_Tail')
for g in body.vertex_groups:
    if g.name != 'B_Tail':
        g.remove(tail.tolist())
vg.add(tail.tolist(), 1.0, 'REPLACE')
print('TAIL bone root', np.round(root, 3), 'tip', np.round(tip, 3), 'vertices', len(tail))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
