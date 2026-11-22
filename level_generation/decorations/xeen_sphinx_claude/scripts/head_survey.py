"""Survey of candidate faces: import a creature GLB, list its materials, render the head region (the top 14 % of the
mesh) front and side in Workbench. Usage: blender -b --python head_survey.py -- <out_prefix> <glb> [...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0]
os.makedirs(out_dir, exist_ok=True)
for path in argv[1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    s = bpy.context.scene
    tag = os.path.basename(path)[:-4]
    meshes = [o for o in s.objects if o.type == 'MESH']
    for o in meshes:
        print('MESH', tag, o.name, len(o.data.polygons), [m.name for m in o.data.materials])
    dg = bpy.context.evaluated_depsgraph_get()
    zs = []
    for o in meshes:
        e = o.evaluated_get(dg)
        zs += [(e.matrix_world @ v.co).z for v in e.data.vertices]
    top = max(zs)
    bot = min(zs)
    h = top - bot
    centre = Vector((0, 0, top - 0.07 * h))
    s.render.engine = 'BLENDER_WORKBENCH'
    s.display.shading.light = 'STUDIO'
    s.display.shading.color_type = 'SINGLE'
    s.display.shading.single_color = (0.75, 0.68, 0.55)
    s.display.shading.show_cavity = True
    s.render.resolution_x = s.render.resolution_y = 400
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    s.collection.objects.link(cam)
    s.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 0.2 * h
    for name, az in (('front', 0), ('side', 90), ('q', 35)):
        a = math.radians(az)
        eye = centre + Vector((math.sin(a), -math.cos(a), 0)) * 3 * h
        cam.location = eye
        cam.rotation_euler = (centre - eye).to_track_quat('-Z', 'Y').to_euler()
        s.render.filepath = os.path.join(out_dir, f'{tag}_{name}.png')
        bpy.ops.render.render(write_still=True)
print('HEADS_DONE')
