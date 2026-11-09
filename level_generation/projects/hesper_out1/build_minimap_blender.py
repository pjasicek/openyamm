"""Render Starport Reach's minimap from the written map, with the approved minimap recipe's light and grade
(level_generation/minimaps/approved_recipe.json): north-up orthographic over the whole map, the terrain from the
ODM's heights coloured as the ground draws it (work/ground_colour.png from build_out1.py), the BModels with their
textures (not the invisible colliders) and the big 3D-model buildings (work/minimap_models.json); no small
decorations, actors or shadows.

    blender --background --factory-startup --python level_generation/projects/hesper_out1/build_minimap_blender.py

Writes work/minimap_master.png (2048) and runtime/worlds/hesper/icons_x2/hes_out1.bmp (1024, PNG bytes like the
other worlds' minimaps). Run after build_out1.py, then the stage.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402

RECIPE = json.loads((ROOT / 'level_generation/minimaps/approved_recipe.json').read_text())
SCALE = 1 / 128.0
ART = ROOT / 'design/kreegan_world/art'
native = parse_odm_file(PROJECT / 'runtime/worlds/hesper/maps/hes_out1.odm')['payload']

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# The terrain: 128 x 128 samples, cells split along the anti-diagonal as the game does, plus one more row and column
# repeating the last ones, so the map's whole square is covered (the native grid ends one cell short of it).
heights = native['height_map']
vertices, faces = [], []
for gy in range(129):
    for gx in range(129):
        z = heights[min(gy, 127) * 128 + min(gx, 127)] * 32
        vertices.append(((gx - 64) * 512 * SCALE, (64 - gy) * 512 * SCALE, z * SCALE))
for gy in range(128):
    for gx in range(128):
        a, b, c, d = gy * 129 + gx, gy * 129 + gx + 1, (gy + 1) * 129 + gx, (gy + 1) * 129 + gx + 1
        faces += [(a, c, b), (b, c, d)]
mesh = bpy.data.meshes.new('terrain')
mesh.from_pydata(vertices, [], faces)
uv_layer = mesh.uv_layers.new()
for polygon in mesh.polygons:
    for loop in polygon.loop_indices:
        x, y, _ = vertices[mesh.loops[loop].vertex_index]
        uv_layer.data[loop].uv = (x / SCALE / 65536 + 0.5, y / SCALE / 65536 + 0.5)
mesh.shade_smooth()
terrain = bpy.data.objects.new('terrain', mesh)
scene.collection.objects.link(terrain)


def image_material(name, path, repeat=False):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    bsdf = nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 1.0
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(str(path), check_existing=True)
    texture.extension = 'REPEAT' if repeat else 'EXTEND'
    material.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    return material


terrain.data.materials.append(image_material('ground', PROJECT / 'work/ground_colour.png'))

# The BModels, with their textures (UV 1.0 = the texture's native size, as written).
textures = {}
for folder in ['textures_d0/blv', 'textures_out1/masters', 'textures_interiors/masters']:
    for png in (ART / folder).glob('*.png'):
        textures[png.stem] = png
for obj_path in sorted((PROJECT / 'source/models').glob('*.obj')):
    if obj_path.stem == 'colliders':
        continue
    before = set(scene.objects)
    bpy.ops.wm.obj_import(filepath=str(obj_path), forward_axis='Y', up_axis='Z')
    for obj in set(scene.objects) - before:
        for slot in obj.material_slots:
            name = slot.material.name.split('.')[0]
            if name in textures:
                slot.material = image_material('bm_' + name, textures[name], repeat=True)

# The model buildings: each model imported once (glTF's y-up becomes z-up as in the game), then linked copies at
# the decorations' positions, facings and game sizes.
imported = {}
for placement in json.loads((PROJECT / 'work/minimap_models.json').read_text()):
    if placement['model'] not in imported:
        before = set(scene.objects)
        bpy.ops.import_scene.gltf(filepath=placement['model'])
        parts = [obj for obj in set(scene.objects) - before if obj.type == 'MESH']
        for obj in parts:
            obj.hide_render = True
        imported[placement['model']] = parts
    for part in imported[placement['model']]:
        copy = part.copy()
        copy.hide_render = False
        scene.collection.objects.link(copy)
        copy.parent = None
        copy.matrix_world = (Matrix.Translation(Vector((placement['x'], placement['y'], placement['z'])) * SCALE)
                             @ Matrix.Rotation(math.radians(placement['facing']), 4, 'Z')
                             @ Matrix.Scale(placement['scale'] * SCALE, 4) @ part.matrix_world)

# Light and camera: the recipe's north-west sun, its strength and no cast shadows. Hesper deviates in colour: a
# neutral sun and a grey fill, since the recipe's warm sun and blue sky (chosen for MM's green maps) turn the violet
# ash brown; the ground keeps the colours it is drawn with in the game.
sun_recipe = RECIPE['sun']
azimuth = math.radians(sun_recipe['azimuth_degrees_clockwise_from_north'])
elevation = math.radians(sun_recipe['elevation_degrees'])
toward_sun = Vector((math.sin(azimuth) * math.cos(elevation), math.cos(azimuth) * math.cos(elevation),
                     math.sin(elevation)))
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = sun_recipe['strength']
sun.data.color = (1.0, 1.0, 1.0)
sun.data.use_shadow = sun_recipe['cast_shadows']
sun.rotation_euler = (-toward_sun).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(sun)
world = bpy.data.worlds.new('world')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.8, 0.8, 0.85, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = RECIPE['world']['strength']
scene.world = world
camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 65536 * SCALE
camera.data.clip_end = 1000
camera.location = (0, 0, 300)
scene.collection.objects.link(camera)
scene.camera = camera

render = RECIPE['render']
scene.render.engine = 'CYCLES'
scene.cycles.samples = render['samples']
scene.cycles.seed = render['seed']
scene.cycles.diffuse_bounces = render['diffuse_bounces']
scene.cycles.use_denoising = render['denoising']
scene.render.resolution_x = scene.render.resolution_y = render['size']
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
(PROJECT / 'work').mkdir(exist_ok=True)
master = PROJECT / 'work/minimap_raw.png'
scene.render.filepath = str(master)
bpy.ops.render.render(write_still=True)
print('MINIMAP_RAW', master)
