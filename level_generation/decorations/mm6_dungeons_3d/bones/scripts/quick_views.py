"""Quick untextured orthographic views of a .blend's meshes (or a GLB) for shape checks: front, side, top,
three-quarter. Usage: blender --background <file.blend> --python quick_views.py -- <out prefix> [glb]"""
import math
import os
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
prefix = args[0]
if len(args) > 1:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=args[1])
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.render.resolution_x = scene.render.resolution_y = 640
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
meshes = [o for o in scene.objects if o.type == 'MESH']
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
centre = (lo + hi) / 2; size = max(hi - lo)
world = scene.world or bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND').inputs['Strength'].default_value = 0.4
sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3; sun.rotation_euler = (math.radians(35), 0, math.radians(-30))
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size * 1.1
for name, yaw, elevation in (('front', 0, 0), ('side', 90, 0), ('top', 0, 89.9), ('tq', 40, 20)):
    y, e = math.radians(yaw), math.radians(elevation)
    d = Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e)))
    cam.location = centre + d * size * 3
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{prefix}_{name}.png'
    bpy.ops.render.render(write_still=True)
print('VIEWS', prefix, [round(v, 3) for v in lo], [round(v, 3) for v in hi])
