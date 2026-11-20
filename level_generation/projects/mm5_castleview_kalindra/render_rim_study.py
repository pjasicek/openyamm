"""Inspect actual rim-study renders over the current textured terrain; collision faces stay hidden."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
OUTPUT = PROJECT/'review'/globals().get('REVIEW_VERSION', 'rim_geometry_study_v5')
sys.path.insert(0, str(PROJECT))
from author_props import ground_at

previous_scene = bpy.context.window.scene
scene = bpy.data.scenes['MM5 world rim geometry study']
bpy.context.window.scene = scene
for obj in list(scene.objects):
    if obj.get('levelgen_kind') == 'review':
        bpy.data.objects.remove(obj, do_unlink=True)


def review_object(name, data):
    obj = bpy.data.objects.new(name, data)
    obj['levelgen_kind'] = 'review'
    scene.collection.objects.link(obj)
    return obj


source = json.loads((PROJECT/'implementation/source/mm5_sw.terrain.yml').read_text())
height, tiles = [bytes.fromhex(source[k+'_hex']) for k in ['height_map', 'tile_map']]
palette = json.loads((PROJECT/'implementation/terrain_palette.json').read_text())['localTileByTexture']
names = {v: k for k, v in palette.items()}
paths = {p.stem.lower(): p for folder in [ROOT/'assets_dev/worlds/mm7/textures',
                                        ROOT/'assets_dev/worlds/mm8/textures',
                                        PROJECT/'implementation/runtime/worlds/mm5/textures']
         for p in folder.iterdir() if p.is_file()}
materials = {}
for name in sorted({names[t] for t in tiles}-{'mm5void'}):
    mat = bpy.data.materials.new('Rim terrain '+name)
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(paths[name]), check_existing=True)
    tex.interpolation = 'Closest'
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = 1
    mat.node_tree.links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    if name.startswith('wtrdr'):
        # Match the native shore's keyed water composition in the preview shader, without changing any bitmap.
        water = mat.node_tree.nodes.new('ShaderNodeTexImage')
        water.image = bpy.data.images.load(str(paths['wtrtyl']), check_existing=True)
        water.interpolation = 'Closest'
        channels = mat.node_tree.nodes.new('ShaderNodeSeparateColor')
        mat.node_tree.links.new(tex.outputs['Color'], channels.inputs['Color'])
        masks = []
        for channel, operation, threshold in [('Red', 'GREATER_THAN', .78), ('Green', 'LESS_THAN', .31),
                                               ('Blue', 'GREATER_THAN', .78)]:
            mask = mat.node_tree.nodes.new('ShaderNodeMath')
            mask.operation = operation
            mask.inputs[1].default_value = threshold
            mat.node_tree.links.new(channels.outputs[channel], mask.inputs[0])
            masks.append(mask.outputs[0])
        for other in masks[1:]:
            product = mat.node_tree.nodes.new('ShaderNodeMath')
            product.operation = 'MULTIPLY'
            mat.node_tree.links.new(masks[0], product.inputs[0])
            mat.node_tree.links.new(other, product.inputs[1])
            masks[0] = product.outputs[0]
        mix = mat.node_tree.nodes.new('ShaderNodeMixRGB')
        mat.node_tree.links.new(masks[0], mix.inputs[0])
        mat.node_tree.links.new(tex.outputs['Color'], mix.inputs[1])
        mat.node_tree.links.new(water.outputs['Color'], mix.inputs[2])
        mat.node_tree.links.new(mix.outputs[0], shader.inputs['Base Color'])
    materials[name] = mat
vertices = [((c-64)*4, (64-r)*4, height[r*128+c]/4) for r in range(128) for c in range(128)]
faces, keys = [], []
for r in range(127):
    for c in range(127):
        name = names[tiles[r*128+c]]
        if name == 'mm5void':
            continue
        i = r*128+c
        faces.extend([(i, i+128, i+1), (i+129, i+1, i+128)])
        keys.extend([name, name])
mesh = bpy.data.meshes.new('Rim exact native heightfield')
mesh.from_pydata(vertices, [], faces)
for mat in materials.values():
    mesh.materials.append(mat)
indices = {key: i for i, key in enumerate(materials)}
uv = mesh.uv_layers.new()
for i, (poly, key) in enumerate(zip(mesh.polygons, keys)):
    poly.material_index = indices[key]
    points = [(0, 1), (0, 0), (1, 1)] if i % 2 == 0 else [(1, 0), (1, 1), (0, 0)]
    for loop, point in zip(poly.loop_indices, points):
        uv.data[loop].uv = point
review_object('REVIEW_rim_terrain', mesh)
for obj in bpy.data.scenes['MM5 Castleview architecture'].objects:
    if obj.get('assembly_id') in ['reger', 'reger_crossing', 'source_4_2_7']:
        copied = obj.copy()
        copied['levelgen_kind'] = 'review'
        copied.hide_render = False
        scene.collection.objects.link(copied)
sun = review_object('REVIEW_rim_sun', bpy.data.lights.new('Rim sun', 'SUN'))
sun.data.energy = 2.2
sun.rotation_euler = (.5, -.4, -.6)
scene.world = bpy.data.worlds.new('Rim neutral lower atmosphere')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.44, .49, .53, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .65
camera = review_object('REVIEW_rim_camera', bpy.data.cameras.new('Rim camera'))
camera.data.lens, camera.data.clip_end = 28, 2000
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1100, 760, 100
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'PNG'
views = [('falista_approach', [-13312, -22000, ground_at(height, [-13312, -22000])+176], [-13312, -24500, -600]),
         ('stopped_edge', [-13312, -23002.5, 224], [-13312, -24002.5, -85]),
         ('cliff_oblique', [-15500, -24700, 900], [-13000, -23100, -700]),
         ('river_spill', [-24000, -15200, 1000], [-21500, -12600, -600]),
         ('islet_oblique', [-21000, -21900, 700], [-20100, -18100, -100])]
for name, eye, target in views:
    camera.location = Vector(eye)/128
    camera.rotation_euler = (Vector(target)/128-camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(OUTPUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
(OUTPUT/'cameras.json').write_text(json.dumps({'views': views,
    'limits': 'Source geometry and textured terrain; static water bitmap, no scenery sprites. Obliques may stand outside valid land.'}, indent=2)+'\n')
bpy.context.window.scene = previous_scene
print({'rendered': len(views), 'canonicalSceneChanged': False})
