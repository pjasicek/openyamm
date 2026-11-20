"""Review renders of Hesper item models: work/<icon>.blend (clay, class colours) or work/<icon>_export.glb (textured),
from a three-quarter view 35 degrees up and a low view 12 degrees up, into review/<kind>/<icon>_{high,low}.png.
Usage: blender --background --python review.py -- clay|textured <icon> [icon ...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
SIZE = 512


def setup_scene():
    scene = bpy.context.scene
    for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x = scene.render.resolution_y = SIZE
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('w')
    scene.world = world
    world.use_nodes = True
    background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    background.inputs['Color'].default_value = (0.55, 0.6, 0.7, 1)
    background.inputs['Strength'].default_value = 0.7
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(-30))
    scene.collection.objects.link(sun)
    camera = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    camera.data.type = 'ORTHO'
    scene.collection.objects.link(camera)
    scene.camera = camera
    return scene, camera


def render(icon, kind):
    if kind == 'clay':
        bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, f'{icon}.blend'))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=os.path.join(WORK, f'{icon}_export.glb'))
    scene, camera = setup_scene()
    meshes = [o for o in scene.objects if o.type == 'MESH']
    points = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    centre = (lo + hi) / 2
    radius = (hi - lo).length / 2
    camera.data.ortho_scale = radius * 2.1
    folder = os.path.join(HERE, 'review', kind)
    os.makedirs(folder, exist_ok=True)
    for name, elevation in (('high', 35), ('low', 12)):
        a, e = math.radians(-35), math.radians(elevation)
        direction = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        camera.location = centre + direction * radius * 4
        camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(folder, f'{icon}_{name}.png')
        bpy.ops.render.render(write_still=True)


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    for icon in args[1:]:
        render(icon, args[0])


main()
