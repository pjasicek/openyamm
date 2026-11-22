"""Quick Workbench previews of one object in a .blend or a GLB (untextured with cavity, or textured), from the front
(Blender -Y = glTF +Z), three-quarter, side, back and top, with a low key light from the front-left.
Usage: blender -b --python preview.py -- <out_prefix> <file.blend|file.glb> [object] [tex]"""
import math
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
meshes = [o for o in s.objects if o.type == 'MESH' and (only is None or o.name == only)
          and not o.name.endswith(('_LOD1', '_LOD2', '_LOD3'))]
for o in s.objects:
    o.hide_render = o not in meshes
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
s.display.shading.color_type = 'TEXTURE' if textured else 'SINGLE'
s.display.shading.single_color = (0.78, 0.66, 0.48)
s.display.shading.show_cavity = True
s.display.shading.show_shadows = True
s.render.resolution_x = s.render.resolution_y = 700
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
s.collection.objects.link(cam)
s.camera = cam
cam.data.type = 'ORTHO'
cam.data.ortho_scale = size * 1.08
for name, az, el in (('front', 0, 6), ('q', 40, 12), ('side', 90, 6), ('back', 180, 10), ('top', 0, 80)):
    a, e = math.radians(az), math.radians(el)
    eye = centre + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * size * 3
    cam.location = eye
    cam.rotation_euler = (centre - eye).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = f'{out}_{name}.png'
    bpy.ops.render.render(write_still=True)
print('PREVIEW_DONE')
