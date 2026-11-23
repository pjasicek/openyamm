"""Review renders of the hull pieces on a mock rim: grass land at 1,056, the rim cell's slope down to the edge at 0,
three hull4 pieces and a hull1 in a row along the edge, a black void with a sun. Views: from the land over the edge,
along the rim from the cliff top, from out in the void.
Usage: blender --background --python review_render.py -- <hull4.glb> <hull1.glb> <out_dir>"""
import math
import os
import sys

import bpy
from mathutils import Vector

hull4, hull1, out_dir = sys.argv[sys.argv.index('--') + 1:][:3]
corner = hull4.replace('hull4', 'hullc')
os.makedirs(out_dir, exist_ok=True)
M = 1.0 / 81.7

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.render.resolution_x, scene.render.resolution_y = 960, 600
scene.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('void')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.004, 0.006, 0.016, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
scene.world = world


def place(path, x, turn=0.0):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    for obj in set(bpy.context.scene.objects) - before:
        if obj.parent is None:
            obj.location = (x * M, 0, 0)
            obj.rotation_euler = (obj.rotation_euler[0], obj.rotation_euler[1], math.radians(turn))


# glTF +Z (out) imports as Blender -Y; the void lies toward -Y, the land toward +Y.
for i, x in enumerate((-2048 - 256, -256, 2048 - 256)):
    place(hull4, x)
place(hull1, 2048 + 1024 - 256 - 512 + 256)
# a land corner at the east end (x 3,328): the corner piece turned 45 between -Y (out) and +X, then a run going +Y
place(corner, 3328, 45)
for y in (1024, 3072):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=hull4)
    for obj in set(bpy.context.scene.objects) - before:
        if obj.parent is None:
            obj.location = (3328 * M, y * M, 0)
            obj.rotation_euler = (obj.rotation_euler[0], obj.rotation_euler[1], math.radians(90))

land = bpy.data.meshes.new('land')
w = 4000 * M
w2 = 3328 * M
verts = [(-w, 0, 0), (w2, 0, 0), (w2 - 512 * M, 512 * M, 1056 * M), (-w, 512 * M, 1056 * M),
         (w2 - 512 * M, 9000 * M, 1056 * M), (-w, 9000 * M, 1056 * M), (w2, 9000 * M, 0)]
land.from_pydata(verts, [], [(0, 1, 2, 3), (3, 2, 4, 5), (1, 6, 4, 2)])
obj = bpy.data.objects.new('land', land)
scene.collection.objects.link(obj)
mat = bpy.data.materials.new('grass')
mat.diffuse_color = (0.2, 0.35, 0.12, 1)
mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.18, 0.3, 0.1, 1)
obj.data.materials.append(mat)

sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 4
sun.rotation_euler = (math.radians(50), 0, math.radians(200))
scene.collection.objects.link(sun)

cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
cam.data.lens = 22
scene.collection.objects.link(cam)
scene.camera = cam


def shot(name, at, target):
    cam.location = Vector(at) * M
    direction = Vector(target) * M - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(out_dir, name + '.png')
    bpy.ops.render.render(write_still=True)


shot('over_edge', (0, 650, 1230), (0, -1800, -1500))
shot('corner_from_land', (1200, 650, 1230), (4200, -1500, -1500))
shot('along', (-3500, 700, 1250), (2500, -900, -900))
shot('from_void', (1500, -7000, -600), (0, 0, -800))
