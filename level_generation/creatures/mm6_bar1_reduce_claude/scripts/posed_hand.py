"""Posed clay close-ups of the left hand for the objects of work/ladder.blend (Body = source, Cand_<n>), Standing frame 0
(REA_CLIP/REA_FRAME), front and three-quarter, each object alone. -> review/hands/posed_<object>_<view>.png
Usage: blender -b work/ladder.blend -P posed_hand.py -- <object> [<object> ...]"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
objs = sys.argv[sys.argv.index('--') + 1:]
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
rig.animation_data.action = bpy.data.actions[os.environ.get('REA_CLIP', 'Standing')]; sc.frame_set(int(os.environ.get('REA_FRAME', '0')))
hb = rig.pose.bones['B_L_Hand']; c = rig.matrix_world @ (hb.head + (hb.tail - hb.head) * 1.6)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = .16; sc.render.resolution_x = sc.render.resolution_y = 450
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.show_cavity = True; sc.display.shading.single_color = (.7, .66, .6)
for name in objs:
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o.name != name
    for view, d in {'front': (0, -1, .1), 'q34': (.7, -.7, .2), 'out': (1, 0, .1)}.items():
        dv = Vector(d).normalized(); cam.location = c + dv * 3
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(HERE, 'review/hands', f'posed_{name}_{view}.png'); bpy.ops.render.render(write_still=True)
