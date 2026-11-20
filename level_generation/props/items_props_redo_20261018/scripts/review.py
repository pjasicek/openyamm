"""Back-face-culled review renders of exported props (above, three-quarter, low).
Usage: blender --background --python review.py -- <icon> [...]  -> review/<icon>_<view>.png"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parents[0] / 'items_wip_equipment_geometry_finish/scripts'))
from review_items import set_culling  # noqa: E402

VIEWS = {'above': (270.0, 89.0), 'three_quarter': (300.0, 40.0), 'low': (240.0, 12.0)}
for icon in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(PROJECT / f'work/{icon}_export.glb'))
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in objects:
        for slot in o.material_slots:
            set_culling(slot.material)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.render.resolution_x = scene.render.resolution_y = 400
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('w')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.58, 0.64, 1)
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.0
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(35), math.radians(-20), math.radians(30))
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    centre = sum(points, Vector()) / len(points)
    extent = max((p - centre).length for p in points)
    camera = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = extent * 2.1
    scene.collection.objects.link(camera)
    scene.camera = camera
    for view, (azimuth, elevation) in VIEWS.items():
        a, e = math.radians(azimuth), math.radians(elevation)
        direction = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
        camera.location = centre + direction * extent * 4
        camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y' if elevation < 80 else 'X').to_euler()
        scene.render.filepath = str(PROJECT / f'review/{icon}_{view}.png')
        bpy.ops.render.render(write_still=True)
