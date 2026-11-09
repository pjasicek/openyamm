"""Review renders of item models lying flat: from above (the player looking down at the item), a raised three-quarter
view and nearly edge-on, back faces culled as in game -> review/<family>/<icon>_<view>.png.
Usage: blender --background --python review_items.py -- <family> [icon ...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = {'above': (90.0, 89.0), 'three_quarter': (35.0, 40.0), 'low': (10.0, 8.0), 'underside': (230.0, -35.0)}


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    family, only = args[0], {a for a in args[1:] if not a.startswith('--')}
    clay, checker = '--clay' in args, '--checker' in args
    detail, flat = '--detail' in args, '--without-normal' in args
    work = os.path.join(HERE, 'work', family)
    out_dir = os.path.join(HERE, 'review', family + ('_clay' if clay else '_checker' if checker else '_detail' if detail else '') + ('_flat' if flat else ''))
    os.makedirs(out_dir, exist_ok=True)
    for name in sorted(os.listdir(work)):
        icon = name.replace('_export.glb', '')
        if not name.endswith('_export.glb') or (only and icon not in only):
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=os.path.join(work, name))
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        grid = bpy.data.images.new('UV checker', width=1024, height=1024) if checker else None
        if grid: grid.generated_type = 'COLOR_GRID'
        for o in objects:
            for slot in o.material_slots:
                if clay:
                    m = bpy.data.materials.new('clay'); m.use_nodes = True
                    m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (.36,.36,.36,1)
                    slot.material = m
                if grid:
                    for node in slot.material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image and node.image.colorspace_settings.name == 'sRGB': node.image = grid
                slot.material.use_backface_culling = True
                if flat:
                    for node in slot.material.node_tree.nodes:
                        if node.type == 'NORMAL_MAP': node.inputs['Strength'].default_value = 0
        scene = bpy.context.scene
        for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
            try:
                scene.render.engine = engine
                break
            except TypeError:
                continue
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 32 if detail else 12
        scene.cycles.device = 'CPU'
        scene.render.threads_mode = 'FIXED'
        scene.render.threads = 6
        scene.render.resolution_x = scene.render.resolution_y = 768 if detail else 320
        scene.render.film_transparent = True
        scene.view_settings.view_transform = 'Standard'
        world = scene.world or bpy.data.worlds.new('World')
        scene.world = world
        world.use_nodes = True
        background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
        background.inputs['Color'].default_value = (0.6, 0.65, 0.75, 1.0)
        if detail: background.inputs['Strength'].default_value = .15
        sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
        sun.data.energy = 3.0
        scene.collection.objects.link(sun)
        sun.rotation_euler = (math.radians(35), math.radians(-20), math.radians(30))
        points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
        centre = sum(points, Vector()) / len(points)
        extent = max((p - centre).length for p in points)
        camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = extent * 2.2
        scene.collection.objects.link(camera)
        scene.camera = camera
        views = {'raking_left': (35, 40), 'raking_right': (35, 40)} if detail else VIEWS
        for view, (azimuth, elevation) in views.items():
            if detail:
                sun.rotation_euler = (math.radians(65), math.radians(-20), math.radians(30 if view == 'raking_left' else 210))
            a, e = math.radians(azimuth), math.radians(elevation)
            direction = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
            camera.location = centre + direction * extent * 4.0
            forward = (centre - camera.location).normalized()
            camera.rotation_euler = forward.to_track_quat('-Z', 'Y' if elevation < 80 else 'X').to_euler()
            scene.render.filepath = os.path.join(out_dir, f'{icon}_{view}.png')
            bpy.ops.render.render(write_still=True)
    print('REVIEW', out_dir)


main()
