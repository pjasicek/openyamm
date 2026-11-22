"""Render candidate source models (one quarter view each). Usage: blender -b --python look.py -- out.png a.glb b.glb ..."""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out, paths = argv[0], argv[1:]
for i, p in enumerate(paths):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    sc = bpy.context.scene
    meshes = [o for o in sc.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(q[k] for q in pts) for k in range(3)])
    hi = Vector([max(q[k] for q in pts) for k in range(3)])
    print('BOUNDS', p, [round(x * 100, 1) for x in lo], [round(x * 100, 1) for x in hi])
    c = (lo + hi) / 2
    r = (hi - lo).length * 1.3
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    d = Vector((0.6, -0.8, 0.45)).normalized()
    cam.location = c + d * r
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 4
    sun.rotation_euler = (math.radians(45), 0, math.radians(30))
    sc.collection.objects.link(sun)
    sc.world = bpy.data.worlds.new('w')
    sc.world.color = (0.3, 0.3, 0.32)
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = 400
    sc.render.filepath = f'{out}_{i}.png'
    bpy.ops.render.render(write_still=True)
