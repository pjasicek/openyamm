"""Clay renders (workbench, cavity) of a .blend's Body at a clip frame: front, back, three-quarter, right forearm
close-up. Usage: blender -b <blend> -P clay_views.py -- <out prefix> [clip:frame, default Standing:0]"""
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]; clip, frame = (args[1] if len(args) > 1 else 'Standing:0').split(':')
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
if not any(m.type == 'ARMATURE' for m in body.modifiers):
    a = body.modifiers.new('Armature', 'ARMATURE'); a.object = rig
act = bpy.data.actions[clip]; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
sc.frame_set(int(frame))
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body:
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
sc.render.resolution_x, sc.render.resolution_y = 700, 900
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 60
hand = rig.matrix_world @ rig.pose.bones['B_R_Hand'].head
shots = {'front': (Vector((0, -4.2, 1.0)), Vector((0, 0, 1.0))),
         'back': (Vector((0, 4.2, 1.0)), Vector((0, 0, 1.0))),
         'q34': (Vector((2.6, -3.2, 1.3)), Vector((0, 0, 1.0))),
         'head': (Vector((0.5, -1.2, 1.75)), Vector((0, 0, 1.62))),
         'rforearm': (hand + Vector((-0.6, -0.7, 0.25)), hand + Vector((0, 0, 0.12)))}
for k, (p, t) in shots.items():
    cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{k}.png'; bpy.ops.render.render(write_still=True)
