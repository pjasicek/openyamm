"""Preview grass clumps built from atlas cells 0 and 1, the way the engine draws the short grass from plants_v4.

A clump is five card quads (the 256 x 192 cell's aspect) in a star around the tuft centre: card k faces
72 x k degrees and leans outward by LEAN degrees about its bottom edge. Cards use cells 0, 1, 0, 1, 0, are unlit
(emission of the texel colour, as the cell colour is matched to the lit ground) and alpha tested at 0.5. The ground
is a flat plane of the short-grass target colour, so a dark base strip or bright card edges stand out.
Renders one clump and a small patch of clumps from eye level (10 degrees down), 45 degrees down and straight down.
Writes <out>/<label>_<scene>_<view>.png.
Usage: blender --background --python preview_clump.py -- <atlas.png> <label> <out dir>
"""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grass_scene  # noqa: E402

LEAN = 25.0
CARD_WIDTH = 0.6
CARD_HEIGHT = CARD_WIDTH * 192 / 256
# The ground under the short grass: SHORT_GRASS_MEAN without the cards' 8 % lift (process_art.py).
GROUND = (0.313 / 1.08, 0.383 / 1.08, 0.218 / 1.08)
VIEWS = {'eye': 10, 'mid': 45, 'top': 90}


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def card_material(atlas):
    material = bpy.data.materials.new('Card')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    texture = tree.nodes.new('ShaderNodeTexImage')
    texture.image = atlas
    texture.interpolation = 'Linear'
    emission = tree.nodes.new('ShaderNodeEmission')
    tree.links.new(texture.outputs['Color'], emission.inputs['Color'])
    clip = tree.nodes.new('ShaderNodeMath')
    clip.operation = 'GREATER_THAN'
    clip.inputs[1].default_value = 0.5
    tree.links.new(texture.outputs['Alpha'], clip.inputs[0])
    transparent = tree.nodes.new('ShaderNodeBsdfTransparent')
    mix = tree.nodes.new('ShaderNodeMixShader')
    tree.links.new(clip.outputs[0], mix.inputs['Fac'])
    tree.links.new(transparent.outputs[0], mix.inputs[1])
    tree.links.new(emission.outputs[0], mix.inputs[2])
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(mix.outputs[0], output.inputs['Surface'])
    material.surface_render_method = 'DITHERED'
    material.use_backface_culling = False
    return material


def ground_material():
    material = bpy.data.materials.new('Ground')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    emission = tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (*[srgb_to_linear(c) for c in GROUND], 1)
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(emission.outputs[0], output.inputs['Surface'])
    return material


def clump(material, origin, yaw, scale, cells):
    """Five leaning cards around origin; returns the mesh object."""
    vertices, faces, uvs = [], [], []
    ground_row = 190 / 192
    for k, cell in enumerate(cells):
        u0, u1 = cell % 4 / 4, (cell % 4 + 1) / 4
        v1 = 1 - cell // 4 / 4
        v0 = v1 - 1 / 4
        facing = math.radians(yaw + 72 * k)
        # The card spans x across, z up, and leans towards +y (its outward side) about its bottom edge.
        bottom = -CARD_HEIGHT * (1 - ground_row)
        corners = [(-CARD_WIDTH / 2, 0, bottom), (CARD_WIDTH / 2, 0, bottom),
                   (CARD_WIDTH / 2, 0, bottom + CARD_HEIGHT), (-CARD_WIDTH / 2, 0, bottom + CARD_HEIGHT)]
        transform = (Matrix.Translation(origin) @ Matrix.Rotation(facing, 4, 'Z') @ Matrix.Scale(scale, 4)
                     @ Matrix.Rotation(math.radians(LEAN), 4, 'X'))
        base = len(vertices)
        vertices += [transform @ Vector(c) for c in corners]
        faces.append((base, base + 1, base + 2, base + 3))
        uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    mesh = bpy.data.meshes.new('Clump')
    mesh.from_pydata(vertices, [], faces)
    layer = mesh.uv_layers.new(name='UVMap')
    for loop in mesh.loops:
        layer.data[loop.index].uv = uvs[loop.vertex_index]
    mesh.materials.append(material)
    obj = bpy.data.objects.new('Clump', mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    atlas_path, label, out = sys.argv[sys.argv.index('--') + 1:][:3]
    grass_scene.reset()
    scene = bpy.context.scene
    grass_scene.eevee(scene, (640, 480))
    scene.render.image_settings.color_depth = '8'
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new('World')
    scene.world.use_nodes = True
    sky = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
    sky.inputs['Color'].default_value = (0.45, 0.6, 0.8, 1)
    atlas = bpy.data.images.load(atlas_path)
    atlas.alpha_mode = 'STRAIGHT'
    material = card_material(atlas)
    bpy.ops.mesh.primitive_plane_add(size=600)
    bpy.context.active_object.data.materials.append(ground_material())
    camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    camera.data.lens = 50
    camera.data.clip_end = 1000
    scene.collection.objects.link(camera)
    scene.camera = camera

    single = [clump(material, (0, 0, 0), 10, 1.0, [0, 1, 0, 1, 0])]
    rng = random.Random(7)
    patch = []
    for _ in range(9):
        origin = (rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1), 0)
        patch.append(clump(material, origin, rng.uniform(0, 72), rng.uniform(0.75, 1.15),
                           [rng.choice((0, 1)) for _ in range(5)]))
    for name, objects, distance, target in (('single', single, 2.2, 0.16), ('patch', patch, 5.0, 0.1)):
        for obj in single + patch:
            obj.hide_render = obj not in objects
        for view, pitch in VIEWS.items():
            grass_scene.aim(camera, (0, 0, target if pitch < 80 else 0), 30, pitch, distance)
            grass_scene.save(scene, os.path.join(out, f'{label}_{name}_{view}.png'))


if __name__ == '__main__':
    main()
