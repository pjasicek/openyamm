"""Re-import source GLBs and render above/low views with opaque back faces culled.

blender --background --python render_batch.py -- baseline|replacement [icon ...]
"""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]


def render(path, destination):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    lower = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    upper = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    centre = (lower + upper) / 2
    extent = max(upper - lower)
    for obj in objects:
        for slot in obj.material_slots:
            slot.material.use_backface_culling = True
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32 if any(o.name.endswith('_glass') for o in objects) else 12
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 6
    scene.render.resolution_x = scene.render.resolution_y = 256
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('Soft studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .57, .7, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
    scene.world = world
    for name, position, energy, size in [
        ('Key', (-2, -3, 5), 350, 4), ('Rim', (2, 1, 3), 250, 3),
    ]:
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA'))
        scene.collection.objects.link(light)
        light.location = centre + Vector(position) * extent
        light.data.energy = energy * extent ** 2
        light.data.shape = 'DISK'
        light.data.size = size * extent
        light.rotation_euler = (centre - light.location).to_track_quat('-Z', 'Y').to_euler()
    camera = bpy.data.objects.new('Review camera', bpy.data.cameras.new('Review camera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = extent * 1.3
    camera.data.clip_start = .001
    destination.parent.mkdir(parents=True, exist_ok=True)
    for name, direction in [('above', (0, -.01, 1)), ('low', (1, -1.8, 1))]:
        camera.location = centre + Vector(direction).normalized() * extent * 4
        camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(destination.with_name(destination.name + '_' + name + '.png'))
        bpy.ops.render.render(write_still=True)


args = sys.argv[sys.argv.index('--') + 1:]
mode, only = args[0], set(args[1:])
assert mode in ('baseline', 'replacement')
for row in json.loads((PROJECT / 'ownership.json').read_text()):
    icon = row['icon']
    if only and icon not in only:
        continue
    path = (ROOT / 'assets_source/engine/world_items/models' / f'item_{icon}.glb' if mode == 'baseline'
            else PROJECT / 'work/exports' / f'jewellery_{icon}_export.glb')
    destination = PROJECT / 'review' / mode / icon
    last_render = destination.with_name(icon + '_low.png')
    if path.exists() and (not last_render.exists() or path.stat().st_mtime > last_render.stat().st_mtime):
        render(path, destination)
    print('REVIEWED', mode, icon, flush=True)
