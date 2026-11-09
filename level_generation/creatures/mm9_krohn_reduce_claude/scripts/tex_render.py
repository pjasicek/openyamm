"""Textured rest renders of a GLB (Workbench, texture colour, rig in rest pose) -> review/<out>/<view>.png: body front/back/side,
belt, knees, forearms, head. Usage: blender -b -P tex_render.py -- <glb> <out dir name>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(argv[0]))
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        if o.animation_data: o.animation_data.action = None
        for b in o.pose.bones: b.matrix_basis.identity()
    if o.type == 'MESH' and o.name not in ('Krohn',):
        o.hide_render = True
sc = bpy.context.scene
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 900
out = os.path.join(HERE, 'review', argv[1]); os.makedirs(out, exist_ok=True)
shots = [('body_front', (0, 0, 1.4), (0, -1, 0), 3.0), ('body_back', (0, 0, 1.4), (0, 1, 0), 3.0), ('body_side', (0, 0, 1.4), (-1, 0, 0), 3.0),
         ('belt', (0, 0, 1.6), (0, -1, 0), 0.9), ('knees', (0, 0, 0.75), (0, -1, 0), 0.9), ('forearm_R', (-0.85, 0, 1.75), (0, -1, 0), 0.7),
         ('forearm_L', (0.85, 0, 1.75), (0, -1, 0), 0.7), ('chest', (0, 0, 2.1), (0, -1, 0), 0.9), ('head', (0, 0, 2.45), (0, -1, 0), 0.9)]
for name, c, dv, s in shots:
    c = Vector(c); cam.data.ortho_scale = s; cam.location = c + Vector(dv).normalized() * 4
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, name + '.png'); bpy.ops.render.render(write_still=True)
print('RENDERED', out)
