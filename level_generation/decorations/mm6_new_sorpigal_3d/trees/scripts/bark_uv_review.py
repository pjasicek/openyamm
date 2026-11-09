"""Before/after renders for fix_bark_uv.py: the whole tree and a bark close-up (lower trunk and limbs), Eevee, sun and
sky, textures as imported from the GLB. Writes <out_prefix>_<label>_<view>.png.
Usage: blender -b -P bark_uv_review.py -- <out_prefix> <label>=<glb> [<label>=<glb> ...]"""
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
prefix = args[0]
for item in args[1:]:
    label, path = item.split('=', 1)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    for o in list(bpy.data.objects):          # LOD levels and the impostor are linked by extras: keep LOD0 only
        if o.type == 'MESH' and o.data.name not in ('Tree', 'Plant') and o.name not in ('Tree', 'Plant'):
            bpy.data.objects.remove(o, do_unlink=True)
    ob = next(o for o in bpy.data.objects if o.type == 'MESH')
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    h = (hi - lo).z
    sc = bpy.context.scene
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            sc.render.engine = engine; break
        except TypeError:
            continue
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.6
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3.4; sun.rotation_euler = (math.radians(45), 0, math.radians(-35))
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    for view, scale, target, res in (('tree', 1.08 * h, Vector((0, 0, h * 0.5)), 520),
                                     ('bark', 0.3 * h, Vector((0, 0, h * 0.2)), 520)):
        d = Vector((0.35, -1.0, 0.12)).normalized()
        cam.location = target + d * h * 3; cam.data.clip_end = h * 10
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = scale
        sc.render.resolution_x = sc.render.resolution_y = res
        sc.render.filepath = f'{prefix}_{label}_{view}.png'
        bpy.ops.render.render(write_still=True)
    print('REVIEWED', label, path)
