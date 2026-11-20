"""Re-import each export and render above, three-quarter and low views with back faces removed (Cycles needs the
explicit Backfacing mix), in the jewellery batch's soft studio light.
blender --background --python review.py -- <tag> [icon ...]   -> review/<tag>/<icon>_<view>.png"""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parents[0] / 'items_wip_equipment_geometry_finish/scripts'))
from review_items import set_culling  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
tag, icons = args[0], args[1:] or ['7item146', '7item154', '7item264', 'quill']
for icon in icons:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(PROJECT / f'work/exports/item_{icon}_export.glb'))
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for obj in objects:
        for slot in obj.material_slots:
            if slot.material.blend_method == 'OPAQUE' or not obj.name.endswith('_glass'):
                set_culling(slot.material)
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    lower = Vector([min(p[i] for p in points) for i in range(3)])
    upper = Vector([max(p[i] for p in points) for i in range(3)])
    centre, extent = (lower + upper) / 2, max(upper - lower)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 384
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('Soft studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .57, .7, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
    scene.world = world
    for name, position, energy, size in [('Key', (-2, -3, 5), 350, 4), ('Rim', (2, 1, 3), 250, 3)]:
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA'))
        scene.collection.objects.link(light)
        light.location = centre + Vector(position) * extent
        light.data.energy = energy * extent ** 2
        light.data.size = size * extent
        light.rotation_euler = (centre - light.location).to_track_quat('-Z', 'Y').to_euler()
    camera = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = extent * 1.3
    camera.data.clip_start = .001
    for view, direction in [('above', (0, -.01, 1)), ('three_quarter', (.6, -1, 1.2)), ('low', (1, -1.8, .5))]:
        camera.location = centre + Vector(direction).normalized() * extent * 4
        camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(PROJECT / f'review/{tag}/{icon}_{view}.png')
        bpy.ops.render.render(write_still=True)
    print('REVIEWED', icon, flush=True)
