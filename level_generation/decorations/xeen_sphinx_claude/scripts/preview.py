"""Quick Workbench previews of GLB/blend models (survey and iteration): front, three-quarter, side, back, top, and
optionally textured. Usage: blender -b --python preview.py -- <out_prefix> <file.glb|file.blend> [obj_prefix] [tex]
Views are from the model's front (glTF +Z = Blender -Y)."""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out, path = argv[0], argv[1]
only = argv[2] if len(argv) > 2 and argv[2] != '-' else None
textured = 'tex' in argv[3:]
if path.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=path)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
s = bpy.context.scene
meshes = [o for o in s.objects if o.type == 'MESH' and (only is None or o.name.startswith(only))
          and not o.name.endswith(('_LOD1', '_LOD2', '_LOD3'))]
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
print('BOUNDS', tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
s.render.engine = 'BLENDER_WORKBENCH'
s.display.shading.light = 'STUDIO'
s.display.shading.color_type = 'TEXTURE' if textured else 'SINGLE'
s.display.shading.single_color = (0.75, 0.68, 0.55)
s.display.shading.show_cavity = True
s.display.shading.show_shadows = True
s.render.resolution_x = s.render.resolution_y = 640
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
s.collection.objects.link(cam)
s.camera = cam
cam.data.type = 'ORTHO'
cam.data.ortho_scale = size * 1.1
for name, az, el in (('front', 0, 8), ('q', 40, 15), ('side', 90, 5), ('back', 180, 10), ('top', 0, 89)):
    a = math.radians(az)
    e = math.radians(el)
    d = size * 3
    eye = centre + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
    cam.location = eye
    cam.rotation_euler = (centre - eye).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = f'{out}_{name}.png'
    bpy.ops.render.render(write_still=True)
print('PREVIEW_DONE')
