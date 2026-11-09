"""Render the two clump cards (plants atlas cells 0 and 1) from the Poly Haven grass_medium_01 model.

A card is an orthographic side view of a bunch of blades from one narrow base: one or two of the model's smaller
tufts, each turned by its own yaw about the shared base, merged into one mesh. Blades (loose mesh parts) are
dropped when they
  - lie on the ground (top below MIN_TOP): dead blades that would make a flat, pale or dark streak at the base;
  - are dead leaf sheaths (texture strip red >= green and darker than DARK): the dark knot at the base;
  - reach farther than the card's max_reach from the base: the sprawling side blades that make a wide, low card;
  - rise above the card's max_top: seed stalks, which would stretch the short grass into wisps.
Flat soft light: a uniform white world plus a weak shadowless top sun. Transparent film, alpha clipped at 0.5 like
the game's alpha test. Writes renders/card<N>.png (1024 x 1024, straight-alpha RGBA, base in the middle column) viewed along +Y;
process_art.py turns them into atlas cells.
Usage: blender --background --python render_cards.py -- <grass_medium_01 glTF dir>
"""
import collections
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grass_scene  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOLUTION = 1024
MIN_TOP = 0.03
DARK = 0.07
# parts: (tuft variant, i.e. node grass_medium_01_<variant>_LOD0, yaw in degrees); max_reach, max_top in metres.
CARDS = {
    0: {'parts': [('mid_c', 90), ('mid_b', 20)], 'max_reach': 0.105, 'max_top': 0.14},
    1: {'parts': [('small_a', 0), ('small_b', 130), ('mid_b', 220)], 'max_reach': 0.08, 'max_top': 0.12},
}


def strip_colours(image):
    """Function mapping a face to the mean diffuse colour under its UVs."""
    width, height = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(height, width, 4)

    def colour(faces, uv):
        samples = [pixels[int(loop[uv].uv.y % 1 * (height - 1)), int(loop[uv].uv.x % 1 * (width - 1)), :3]
                   for face in faces for loop in face.loops]
        return np.mean(samples, axis=0)
    return colour


def blades(mesh):
    """Loose parts of a bmesh as lists of faces."""
    parent = list(range(len(mesh.verts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for edge in mesh.edges:
        a, b = find(edge.verts[0].index), find(edge.verts[1].index)
        if a != b:
            parent[a] = b
    parts = collections.defaultdict(list)
    for face in mesh.faces:
        parts[find(face.verts[0].index)].append(face)
    return list(parts.values())


def build_card(objects, card, colour):
    """One mesh object at the origin: the card's tufts turned by their yaws, without the dropped blades."""
    mesh = bmesh.new()
    for variant, yaw in card['parts']:
        source = objects[f'grass_medium_01_{variant}_LOD0']
        part = bmesh.new()
        part.from_mesh(source.data)
        part.verts.ensure_lookup_table()
        uv = part.loops.layers.uv.active
        drop = []
        counts = collections.Counter()
        for faces in blades(part):
            verts = {v for f in faces for v in f.verts}
            top = max(v.co.z for v in verts)
            reach = max(math.hypot(v.co.x, v.co.y) for v in verts)
            mean = colour(faces, uv)
            if top < MIN_TOP:
                counts['lying'] += 1
            elif mean[0] >= mean[1] and mean.max() < DARK:
                counts['dead sheath'] += 1
            elif reach > card['max_reach']:
                counts['sprawling'] += 1
            elif top > card['max_top']:
                counts['seed stalk'] += 1
            else:
                counts['kept'] += 1
                continue
            drop += faces
        bmesh.ops.delete(part, geom=drop, context='FACES')
        bmesh.ops.delete(part, geom=[v for v in part.verts if not v.link_faces], context='VERTS')
        bmesh.ops.transform(part, matrix=Matrix.Rotation(math.radians(yaw), 4, 'Z'), verts=part.verts)
        print('CARD part', variant, yaw, dict(counts))
        temp = bpy.data.meshes.new('part')
        part.to_mesh(temp)
        part.free()
        mesh.from_mesh(temp)
        bpy.data.meshes.remove(temp)
    data = bpy.data.meshes.new('card')
    mesh.to_mesh(data)
    mesh.free()
    data.materials.append(objects[f'grass_medium_01_{card["parts"][0][0]}_LOD0'].material_slots[0].material)
    obj = bpy.data.objects.new('card', data)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    source = args[0]
    grass_scene.reset()
    scene = bpy.context.scene
    grass_scene.eevee(scene, (RESOLUTION, RESOLUTION))
    scene.render.image_settings.color_depth = '8'
    grass_scene.flat_light(scene)
    objects = grass_scene.import_grass(os.path.join(source, 'grass_medium_01_2k.gltf'),
                                       os.path.join(source, 'textures/grass_medium_01_alpha_2k.png'))
    for obj in objects.values():
        obj.hide_render = True
    colour = strip_colours(next(i for i in bpy.data.images if 'diff' in i.name))
    camera = grass_scene.ortho_camera(scene)
    previous = None
    for index, card in CARDS.items():
        if previous:
            previous.hide_render = True
        obj = previous = build_card(objects, card, colour)
        corners = [Vector(c) for c in obj.bound_box]
        low = Vector([min(c[i] for c in corners) for i in range(3)])
        high = Vector([max(c[i] for c in corners) for i in range(3)])
        # Centred on the base (the tuft's vertical axis), so the card's middle column is the clump centre.
        size = max(2 * max(-low.x, high.x), high.z - low.z) * 1.05
        camera.data.ortho_scale = size
        grass_scene.aim(camera, (0, 0, (low.z + high.z) / 2), 0, 0, 3)
        grass_scene.save(scene, os.path.join(HERE, 'renders', f'card{index}.png'))
        print('CARD', index, card, 'frame', round(size, 4), 'm')


if __name__ == '__main__':
    main()
