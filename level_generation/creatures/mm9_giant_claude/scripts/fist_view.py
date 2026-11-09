"""Diagnosis: apply work/hand_poses.json (bone-local deltas) to the rest rig and render the right hand with the mallet. Args: <blend> <poses json> <out prefix> [center] [ortho]"""
import bpy, sys, json
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
P = json.load(open(a[1]))
for pb in rig.pose.bones: pb.matrix_basis.identity(); pb.rotation_mode = 'QUATERNION'
import os
for k in ('grip', 'hand_offset', 'gripL'):
    for n, q in P.get(k, {}).items():
        if n in rig.pose.bones: rig.pose.bones[n].rotation_quaternion = Quaternion((q[3], q[0], q[1], q[2]))
bpy.context.view_layer.update()
if 'Xbase' in rig.pose.bones: rig.pose.bones['Xbase'].matrix = rig.data.bones['Xbase'].matrix_local.copy()     # the mallet stays MM9's (finger_keys_giant.py takes the wrist turn out of Xbase)
bpy.context.view_layer.update()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.78, .76, .72); sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 700
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[4]) if len(a) > 4 else 0.45
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
C = Vector([float(x) for x in a[3].split(',')]) if len(a) > 3 else Vector((-1.05, -0.22, 0.33))
for v, d in {'front': (0, -1, 0), 'out': (-1, 0, 0), 'below': (0, 0, -1), 'q': (-1, -1, 0.5), 'in': (1, -0.3, -0.2), 'axis': (-0.4, 0.89, -0.2)}.items():
    d = Vector(d).normalized(); cam.location = C + d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[2]}_{v}.png'; bpy.ops.render.render(write_still=True)
