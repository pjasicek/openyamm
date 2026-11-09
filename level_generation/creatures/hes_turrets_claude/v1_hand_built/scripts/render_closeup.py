"""Close-up shading check of a turret: the actor GLB at rest on its mount GLB, a raking sun, three views (the
viewer's three-quarter on the head and barrel, a low side view along the barrel, and the mount). Used for the
before/after of the smooth-shading rebuild; renders whatever GLBs it is given.
Args: -- <actor glb> <mount glb> <heavy 0|1> <out prefix>   (writes <out prefix>_<view>.png)"""
import math
import os
import sys

import bpy
from mathutils import Vector

actor, mount, heavy, prefix = sys.argv[sys.argv.index('--') + 1:]
d = 1.35 if heavy == '1' else 1.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(actor))
bpy.ops.import_scene.gltf(filepath=os.path.abspath(mount))
scene = bpy.context.scene
for obj in scene.objects:
    if obj.animation_data:
        obj.animation_data.action = None
    if obj.type == 'ARMATURE':
        for pb in obj.pose.bones:
            pb.matrix_basis.identity()
    if obj.type == 'MESH' and '_LOD' in obj.name:
        obj.hide_render = True
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1200, 800
world = bpy.data.worlds.new('World'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.36, 0.37, 0.40, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(55), 0, math.radians(30))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens = 50


def shot(view, location, target):
    cam.location = Vector(location)
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{prefix}_{view}.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED', scene.render.filepath)


head = (0, -0.75 * d, 1.25 * d)
shot('head', (2.9 * d, -2.9 * d, 2.1 * d), head)                         # the review screenshot's three-quarter
shot('barrel', (1.2 * d, -2.6 * d, 1.55 * d), (0, -1.2 * d, 1.42 * d))  # close along the barrel and rings
shot('mount', (2.2 * d, -2.0 * d, 1.25), (0, 0, 0.65))                   # the pedestal and the turning ring
