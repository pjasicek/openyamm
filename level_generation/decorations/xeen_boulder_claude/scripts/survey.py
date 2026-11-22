"""Survey (Blender): textured Workbench views of candidate source models, front (glTF +Z) and three-quarter.
Usage: blender -b --python survey.py -- <out_dir> <a.glb> [<b.glb> ...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]
for path in argv[1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    s = bpy.context.scene
    meshes = [o for o in s.objects if o.type == 'MESH' and not o.name.endswith(('_LOD1', '_LOD2', '_LOD3'))]
    for o in s.objects:
        if o.type == 'MESH' and o not in meshes:
            o.hide_render = True
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in meshes:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    centre = (lo + hi) / 2
    size = max(hi - lo)
    s.render.engine = 'BLENDER_WORKBENCH'
    s.display.shading.light = 'STUDIO'
    s.display.shading.color_type = 'TEXTURE'
    s.display.shading.show_cavity = True
    s.render.resolution_x = s.render.resolution_y = 360
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    s.collection.objects.link(cam)
    s.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = size * 1.1
    stem = os.path.splitext(os.path.basename(path))[0]
    for name, az, el in (('front', 0, 8), ('q', 45, 15), ('side', 90, 8)):
        a, e = math.radians(az), math.radians(el)
        eye = centre + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * size * 3
        cam.location = eye
        cam.rotation_euler = (centre - eye).to_track_quat('-Z', 'Y').to_euler()
        s.render.filepath = os.path.join(out, f'{stem}_{name}.png')
        bpy.ops.render.render(write_still=True)
    print('SURVEY', stem, tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
print('SURVEY_DONE')
