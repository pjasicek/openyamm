"""Review renders of item models lying flat: from above (the player looking down at the item), a raised three-quarter
view and nearly edge-on, back faces culled as in game -> review/<family>/<icon>_<view>.png.
Usage: blender --background --python review_items.py -- <family> [icon ...]"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = {'above': 89, 'three_quarter': 38, 'low': 8, 'underside': -55}


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    family, only = args[0], set(args[1:])
    clay, checker = '--clay' in only, '--checker' in only
    only -= {'--clay', '--checker'}
    work = os.path.join(HERE, 'work', family)
    out_dir = os.path.join(HERE, 'review', family + ('_clay' if clay else '_checker' if checker else ''))
    os.makedirs(out_dir, exist_ok=True)
    for name in sorted(os.listdir(work)):
        icon = name.replace('_export.glb', '').removeprefix('item_').removeprefix('pole_')
        if not name.endswith('_export.glb') or (only and icon not in only):
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=os.path.join(work, name))
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        if clay or checker:
            material = bpy.data.materials.new('review_override')
            material.use_nodes = True
            bsdf = material.node_tree.nodes.get('Principled BSDF')
            bsdf.inputs['Base Color'].default_value = (0.45, 0.45, 0.45, 1)
            bsdf.inputs['Roughness'].default_value = 0.75
            if checker:
                tile = material.node_tree.nodes.new('ShaderNodeTexChecker')
                tile.inputs['Scale'].default_value = 24
                uv = material.node_tree.nodes.new('ShaderNodeTexCoord')
                material.node_tree.links.new(uv.outputs['UV'], tile.inputs['Vector'])
                material.node_tree.links.new(tile.outputs['Color'], bsdf.inputs['Base Color'])
            for obj in objects:
                obj.data.materials.clear()
                obj.data.materials.append(material)
                for face in obj.data.polygons:
                    face.material_index = 0
        for o in objects:
            for slot in o.material_slots:
                slot.material.use_backface_culling = True
        scene = bpy.context.scene
        for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
            try:
                scene.render.engine = engine
                break
            except TypeError:
                continue
        scene.render.resolution_x, scene.render.resolution_y = 1024, 320
        scene.render.film_transparent = True
        scene.view_settings.view_transform = 'Standard'
        world = scene.world or bpy.data.worlds.new('World')
        scene.world = world
        world.use_nodes = True
        background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
        background.inputs['Color'].default_value = (0.6, 0.65, 0.75, 1.0)
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
        for view, elevation in VIEWS.items():
            e = math.radians(elevation)
            direction = Vector((math.cos(e), 0, math.sin(e)))
            camera.location = centre + direction * extent * 4.0
            right = Vector((0, 1, 0))
            up = direction.cross(right)
            camera.rotation_euler = Matrix((right, up, direction)).transposed().to_euler()
            scene.render.filepath = os.path.join(out_dir, f'{icon}_{view}.png')
            bpy.ops.render.render(write_still=True)
    print('REVIEW', out_dir)


main()
