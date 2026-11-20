"""Render GLBs for review: each model from a raised three-quarter view in soft light, saved as review/<out>/<name>.png.

    blender --background --factory-startup --python scripts/render_review.py -- <out folder name> <glb> [...]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
out = os.path.join(HERE, 'review', args[0])
os.makedirs(out, exist_ok=True)
for path in args[1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [
        e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.render.film_transparent = False
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in scene.objects if o.type == 'MESH']
    points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    centre, size = (lo + hi) / 2, max((hi - lo).length, 0.1)
    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.32, 0.30, 0.34, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    scene.world = world
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    scene.collection.objects.link(sun)
    camera = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = size * 1.15
    direction = Vector((math.sin(math.radians(35)), -math.cos(math.radians(35)), 0.5)).normalized()
    camera.location = centre + direction * size * 3
    camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(camera)
    scene.camera = camera
    scene.render.filepath = os.path.join(out, os.path.splitext(os.path.basename(path))[0] + '.png')
    bpy.ops.render.render(write_still=True)
