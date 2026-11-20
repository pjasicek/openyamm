"""Review renders of one GLB: above, front three-quarter and low, on a neutral background.

blender --background --python review_render.py -- <glb> <output prefix> [plain]
`plain` renders grey clay (shape check of a raw Meshy model); otherwise the GLB's own materials."""
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
glb, prefix, plain = args[0], args[1], 'plain' in args[2:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in points) for i in range(3)])
hi = Vector([max(p[i] for p in points) for i in range(3)])
centre = (lo + hi) / 2
size = max(hi - lo)
if plain:
    clay = bpy.data.materials.new('clay')
    clay.use_nodes = True
    bsdf = next(n for n in clay.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1)
    bsdf.inputs['Roughness'].default_value = 0.6
    for o in meshes:
        o.data.materials.clear()
        o.data.materials.append(clay)
for o in meshes:
    for m in o.data.materials:
        if m:
            m.use_backface_culling = True
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = scene.render.resolution_y = 512
scene.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('w')
scene.world = world
world.use_nodes = True
background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
background.inputs['Color'].default_value = (0.16, 0.17, 0.2, 1)
background.inputs['Strength'].default_value = 1.0
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(40), 0, math.radians(30))
scene.collection.objects.link(sun)
camera = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = size * 1.35
scene.collection.objects.link(camera)
scene.camera = camera
for view, (yaw, pitch) in {'above': (0, 80), 'three_quarter': (35, 30), 'low': (-25, 12)}.items():
    y, p = math.radians(yaw), math.radians(pitch)
    direction = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    camera.location = centre + direction * size * 4
    camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{prefix}_{view}.png'
    bpy.ops.render.render(write_still=True)
print('REVIEW', prefix)
