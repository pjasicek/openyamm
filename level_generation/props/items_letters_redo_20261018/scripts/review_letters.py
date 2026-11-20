"""Back-face-culled review renders of each export (above, three-quarter, low).
Usage: blender --background --python review_letters.py -- [icon ...]   -> review/renders/<icon>_<view>.png"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'items_wip_equipment_geometry_finish/scripts'))
from review_items import set_culling  # noqa: E402

VIEWS = {'above': (270.0, 89.0), 'three_quarter': (300.0, 35.0), 'low': (250.0, 12.0)}
icons = sys.argv[sys.argv.index('--') + 1:]
out = P / 'review/renders'
out.mkdir(parents=True, exist_ok=True)
for icon in icons:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(P / 'work/exports' / f'item_{icon}_export.glb'))
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in objects:
        for slot in o.material_slots:
            set_culling(slot.material)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('w')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.6, 0.62, 0.66, 1)
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
        scene.render.filepath = str(out / f'{icon}_{view}.png')
        bpy.ops.render.render(write_still=True)
