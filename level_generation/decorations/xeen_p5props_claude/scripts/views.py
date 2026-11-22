"""Workbench textured views of GLBs (each its own row): blender -b --python views.py -- <out_prefix> <a.glb> [b.glb ...]
Writes <out_prefix>_<i>_<view>.png. Front = glTF +Z (Blender -Y)."""
import sys, math, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
prefix, files = a[0], a[1:]
for i, f in enumerate(files):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f)
    sc = bpy.context.scene
    obs = [o for o in sc.objects if o.type == 'MESH' and 'LOD' not in o.name]
    for o in sc.objects:
        if o.type == 'MESH' and o not in obs:
            o.hide_render = True
    pts = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
    lo = Vector(map(min, *pts)); hi = Vector(map(max, *pts)); c = (lo + hi) / 2; s = max(hi - lo)
    print('BOUNDS', f, tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.show_cavity = True; sh.color_type = 'TEXTURE'
    sh.background_type = 'VIEWPORT'; sh.background_color = (0.25, 0.27, 0.3)
    sc.render.resolution_x = sc.render.resolution_y = 400
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = s * 1.15
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
    for name, az, el in (('front', 0, 10), ('q', 40, 25), ('side', 90, 10), ('top', 0, 85)):
        r, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(r) * math.cos(e), -math.cos(r) * math.cos(e), math.sin(e)))
        cam.location = c + d * s * 4
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{prefix}_{i}_{name}.png'
        bpy.ops.render.render(write_still=True)
print('VIEWS_DONE')
