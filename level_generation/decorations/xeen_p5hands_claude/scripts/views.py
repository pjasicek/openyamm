"""Workbench clay views of an object in a .blend or a GLB: blender -b [file.blend] --python views.py -- <out_prefix> [glb]"""
import sys, math, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
prefix = a[0]
if len(a) > 1:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=a[1])
sc = bpy.context.scene
obs = [o for o in sc.objects if o.type == 'MESH' and 'LOD' not in o.name]
for o in sc.objects:
    if o.type == 'MESH' and o not in obs: o.hide_render = True
pts = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
lo = Vector(map(min, *pts)); hi = Vector(map(max, *pts)); c = (lo + hi) / 2; s = max(hi - lo)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.show_cavity = True
sh.color_type = 'TEXTURE' if len(a) > 1 else 'SINGLE'; sh.single_color = (0.8, 0.76, 0.66)
sh.background_type = 'VIEWPORT'; sh.background_color = (0.25, 0.27, 0.3)
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = s * 1.15
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for name, az, el in (('front', 0, 8), ('q', 40, 15), ('side', 90, 5), ('top', 0, 80), ('back', 180, 10)):
    r, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(r) * math.cos(e), -math.cos(r) * math.cos(e), math.sin(e)))
    cam.location = c + d * s * 4
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{prefix}_{name}.png'
    bpy.ops.render.render(write_still=True)
print('VIEWS_DONE')
