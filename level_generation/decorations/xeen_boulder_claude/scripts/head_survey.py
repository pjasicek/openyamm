"""Survey of candidate faces (Blender): import a creature GLB in its rest pose and render the head region (top 15 %
of the mesh) front, three-quarter and side in Workbench, untextured with cavity (what survives as carved stone).
Usage: blender -b --python head_survey.py -- <out_dir> <glb> [...]"""
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
    for o in s.objects:
        if o.type == 'ARMATURE':
            o.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    meshes = [o for o in s.objects if o.type == 'MESH' and not o.name.endswith(('_LOD1', '_LOD2', '_LOD3'))]
    for o in s.objects:
        if o.type == 'MESH' and o not in meshes:
            o.hide_render = True
    dg = bpy.context.evaluated_depsgraph_get()
    zs = []
    for o in meshes:
        e = o.evaluated_get(dg)
        zs += [(e.matrix_world @ v.co).z for v in e.data.vertices]
        print('MESH', tag, o.name, len(o.data.polygons))
    top, bot = max(zs), min(zs)
    h = top - bot
    centre = Vector((0, 0, top - 0.075 * h))
    s.render.engine = 'BLENDER_WORKBENCH'
    s.display.shading.light = 'STUDIO'
    s.display.shading.color_type = 'SINGLE'
    s.display.shading.single_color = (0.75, 0.68, 0.55)
    s.display.shading.show_cavity = True
    s.render.resolution_x = s.render.resolution_y = 300
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    s.collection.objects.link(cam)
    s.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 0.2 * h
    for name, az in (('front', 0), ('q', 35), ('side', 90)):
        a = math.radians(az)
        eye = centre + Vector((math.sin(a), -math.cos(a), 0)) * 3 * h
        cam.location = eye
        cam.rotation_euler = (centre - eye).to_track_quat('-Z', 'Y').to_euler()
        s.render.filepath = os.path.join(out_dir, f'{tag}_{name}.png')
        bpy.ops.render.render(write_still=True)
print('HEADS_DONE')
