"""Render candidate poses (front, three-quarter, side) of a creature. Usage:
blender -b --python pose_preview.py -- <src.glb> <specs.json> <outdir>   (specs.json: {name: spec, ...})"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
src, specs_path, outdir = argv
os.makedirs(outdir, exist_ok=True)
specs = json.load(open(specs_path))
for name, spec in specs.items():
    arm, body = posing.import_creature(src)
    posing.apply_pose(arm, spec)
    obj = posing.bake_static(arm, body)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.single_color = (0.55, 0.55, 0.57)
    scene.display.shading.show_cavity = True
    scene.render.resolution_x, scene.render.resolution_y = 400, 500
    cam_data = bpy.data.cameras.new('cam')
    cam_data.type = 'ORTHO'
    cam = bpy.data.objects.new('cam', cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    print('BOUNDS', name, tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
    centre = (lo + hi) / 2
    size = max(hi - lo) * 1.1
    for view, az in (('front', 0), ('q', 35), ('side', 90)):
        a = math.radians(az)
        d = Vector((math.sin(a), -math.cos(a), 0.12)).normalized()
        cam.location = centre + d * size * 3
        cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam_data.ortho_scale = size
        scene.render.filepath = os.path.join(outdir, f'{name}_{view}.png')
        bpy.ops.render.render(write_still=True)
print('PREVIEW_DONE')
