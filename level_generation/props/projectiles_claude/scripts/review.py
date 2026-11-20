"""Review renders of a projectile export, back faces of opaque materials culled as in game: review/<name>/<view>.png.

Views, the arrow pointing along +X on screen like the sprite's side frame: side (sprite frame 2), three-quarter from
the front and above, head-on (frame 0), tail-on (frame 4) and a top view. Orthographic, transparent background.
Usage: blender --background --python review.py -- <name> <export.glb>"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = {
    # name: (azimuth of the camera round the model from its right side, elevation), degrees
    'side': (0.0, 0.0),
    'three_quarter': (-40.0, 20.0),
    'head_on': (-90.0, 0.0),
    'tail_on': (90.0, 0.0),
    'top': (0.0, 89.0),
    'below_back': (130.0, -25.0),
}


def main():
    name, path = sys.argv[sys.argv.index('--') + 1:][:2]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in objects:
        for slot in o.material_slots:
            # Opaque materials are single-sided in game; the blended flame cards are double-sided.
            if slot.material is not None and slot.material.surface_render_method != 'BLENDED':
                slot.material.use_backface_culling = True
    scene = bpy.context.scene
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x, scene.render.resolution_y = 1024, 512
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    world = scene.world or bpy.data.worlds.new('World')
    scene.world = world
    world.use_nodes = True
    background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    background.inputs['Color'].default_value = (0.6, 0.65, 0.75, 1.0)
    background.inputs['Strength'].default_value = 1.0
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 3.0
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(35), math.radians(-20), math.radians(30))
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    centre = sum(points, Vector()) / len(points)
    extent = max((p - centre).length for p in points)
    camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = extent * 2.1
    scene.collection.objects.link(camera)
    scene.camera = camera
    out_dir = os.path.join(HERE, 'review', name)
    os.makedirs(out_dir, exist_ok=True)
    for view, (azimuth, elevation) in VIEWS.items():
        # The model points along Blender -Y; the side view looks from +X... seen with the tip to the right.
        a, e = math.radians(azimuth), math.radians(elevation)
        direction = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
        camera.location = centre + direction * extent * 4.0
        forward = (centre - camera.location).normalized()
        up = Vector((0, 0, 1)) if abs(elevation) < 80 else Vector((-1, 0, 0))
        camera.rotation_euler = forward.to_track_quat('-Z', 'Y').to_euler()
        if abs(elevation) >= 80:
            camera.rotation_euler = forward.to_track_quat('-Z', 'X').to_euler()
        _ = up
        scene.render.filepath = os.path.join(out_dir, f'{view}.png')
        bpy.ops.render.render(write_still=True)
    print('REVIEW', out_dir)


main()
