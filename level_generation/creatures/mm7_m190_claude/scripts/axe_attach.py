"""Review/gate copy of a rig with the modelled axe skinned 100 % to a 'Sword' bone (child of B_R_Hand at
axe_frame.hand_local, the export rule) as piece 1000 / garment 9, so g6_prop.py (PROP_HAND=R), probe and clip scripts
see the exported axe. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import axe_frame
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; scene = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        o.animation_data_create()
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
M = rig.data.bones['B_R_Hand'].matrix_local @ axe_frame.hand_local(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.get('Sword') or rig.data.edit_bones.new('Sword')
eb.head = M.translation; eb.tail = M.translation + M.col[1].xyz * 0.15; eb.align_roll(M.col[2].xyz)
eb.parent = rig.data.edit_bones['B_R_Hand']; eb.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
ax = axe_frame.load_axe(scene)
ax.data.transform(M)
n = len(ax.data.vertices)
ax.vertex_groups.new(name='Sword').add(list(range(n)), 1.0, 'REPLACE')
for at in ('piece', 'garment', 'finger'):
    if at in body.data.attributes:
        ax.data.attributes.new(at, 'INT', 'POINT').data.foreach_set('value', [1000 if at == 'piece' else (9 if at == 'garment' else 0)] * n)
if 'Sword' not in body.vertex_groups:
    body.vertex_groups.new(name='Sword')
for o in bpy.data.objects:
    o.select_set(o in (body, ax))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print('AXEATTACH verts', n)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
