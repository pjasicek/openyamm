"""Untextured (clay, cavity) head close-ups of a master blend's mesh, rest pose: side, back, front, q34, top.
Usage: blender -b -P clay_head.py -- <blend under work/> <object> <tag>"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, name, tag = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
for x in bpy.data.objects: x.hide_render = x.name != name
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .72, .68); sh.show_cavity = True
sh.cavity_type = 'BOTH'; sc.render.resolution_x = sc.render.resolution_y = 700
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
import json
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('CH_SCALE', '.55')); c = Vector(json.loads(os.environ.get('CH_CENTER', '[0, -1.27, 1.0]')))
out = os.path.join(HERE, 'review', 'horns'); os.makedirs(out, exist_ok=True)
for view, d in {'side': (1, 0, .05), 'back': (0, 1, .4), 'front': (0, -1, .15), 'q34': (.8, -.6, .5), 'top': (0, .1, 1)}.items():
    dv = Vector(d).normalized(); cam.location = c + dv * 4
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'clay_{tag}_{view}.png'); bpy.ops.render.render(write_still=True)
