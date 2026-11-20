"""Review renders of item models lying flat: from above (the player looking down at the item), a raised three-quarter
view and nearly edge-on, back faces culled as in game -> review/<family>/<icon>_<view>.png.
Usage: blender --background --python review_items.py -- <family> [icon ...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = {'above': (90.0, 89.0), 'three_quarter': (35.0, 40.0), 'low': (10.0, 8.0), 'front': (90.0, 22.0), 'back': (270.0, 22.0)}


def set_culling(material):
    # Cycles ignores the Eevee-only flag, so remove back faces explicitly in review renders.
    material.use_backface_culling = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = next(node for node in nodes if node.type == 'OUTPUT_MATERIAL')
    surface = output.inputs['Surface'].links[0].from_socket
    geometry = nodes.new('ShaderNodeNewGeometry')
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    mix = nodes.new('ShaderNodeMixShader')
    links.new(geometry.outputs['Backfacing'], mix.inputs[0])
    links.new(surface, mix.inputs[1])
    links.new(transparent.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs['Surface'])


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    family, only = args[0], set(args[1:])
    work = os.path.join(HERE, 'work', family)
    out_dir = os.path.join(HERE, 'review', family)
    os.makedirs(out_dir, exist_ok=True)
    for name in sorted(os.listdir(work)):
        icon = name.replace('_export.glb', '')
        if not name.endswith('_export.glb') or (only and icon not in only):
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=os.path.join(work, name))
        objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        for o in objects:
            for slot in o.material_slots:
                set_culling(slot.material)
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.cycles.samples = 16
        scene.render.resolution_x = scene.render.resolution_y = 384
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
        for view, (azimuth, elevation) in VIEWS.items():
            a, e = math.radians(azimuth), math.radians(elevation)
            direction = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
            camera.location = centre + direction * extent * 4.0
            forward = (centre - camera.location).normalized()
            camera.rotation_euler = forward.to_track_quat('-Z', 'Y' if elevation < 80 else 'X').to_euler()
            scene.render.filepath = os.path.join(out_dir, f'{icon}_{view}.png')
            bpy.ops.render.render(write_still=True)
    print('REVIEW', out_dir)


if __name__ == '__main__':
    main()
