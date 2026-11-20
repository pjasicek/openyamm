"""Blender MCP review of the exact authored terrain palette and existing architecture."""
import json
import hashlib
import csv
from pathlib import Path
import sys

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
OUTPUT = Path(globals().get('REVIEW_OUTPUT', PROJECT/'review/terrain_materials_v1/blender'))
OUTPUT.mkdir(parents=True, exist_ok=True)
previous = bpy.context.window.scene
name = globals().get('REVIEW_SCENE', 'MM5 terrain materials review')
if name in bpy.data.scenes:
    bpy.data.scenes.remove(bpy.data.scenes[name])
scene = bpy.data.scenes.new(name)
bpy.context.window.scene = scene


def object_for(name, data):
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    return obj


native = None
if globals().get('REVIEW_NATIVE', False):
    sys.path.insert(0, str(ROOT/'util'))
    from map_export import parse_odm_file
    native_path = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    native_digest = hashlib.sha256(native_path.read_bytes()).hexdigest()
    build = json.loads((PROJECT/'review/native/build.json').read_text())
    assert native_digest == build['nativeSha256'], 'Wait for the current native build to finish'
    native = parse_odm_file(native_path)['payload']
    height, tiles = [bytes(native[key]) for key in ['height_map', 'tile_map']]
else:
    source = json.loads((PROJECT/'implementation/source/mm5_sw.terrain.yml').read_text())
    height, tiles = [bytes.fromhex(source[key+'_hex']) for key in ['height_map', 'tile_map']]
palette = json.loads((PROJECT/'implementation/terrain_palette.json').read_text())['localTileByTexture']
names = {value: key for key, value in palette.items()}
if native:
    rows = {int(row[0]): row for row in csv.reader(
        (Path(build['stage'])/'assets_dev/engine/data_tables/terrain_tile_data.txt').open(), delimiter='\t')
        if row and row[0].isdigit()}
    assert min(tiles)>=90 and max(tiles)<234, 'This MM5 palette uses four explicit appended banks'
    for tile in set(tiles):
        bank, offset = divmod(tile-90, 36)
        index = native['tile_set_lookup_indices'][bank]+offset
        assert rows[index][1].lower()==names[tile], ('Native terrain registry differs from review palette', tile)
paths = {p.stem.lower(): p for folder in [ROOT/'assets_dev/worlds/mm7/textures',
                                        ROOT/'assets_dev/worlds/mm8/textures',
                                        PROJECT/'implementation/runtime/worlds/mm5/textures']
         for p in folder.iterdir() if p.is_file()}
materials = {}
material_keys = {names[t] for t in tiles}-{'mm5void'}
if native:
    material_keys.update(face['texture_name'].lower() for model in native['bmodels']
                         for face in model['faces'] if not face['attributes'] & 0x2000)
for key in sorted(material_keys):
    mat = bpy.data.materials.new('MM5 terrain review '+key)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(paths[key]), check_existing=True)
    tex.interpolation = 'Closest'
    shader = nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = 1
    color = tex.outputs['Color']
    if key.startswith('wtrdr') or (key.startswith('mm5ac') and key!='mm5acid'):
        water = nodes.new('ShaderNodeTexImage')
        base = 'mm5acid' if key.startswith('mm5ac') else 'wtrtyl'
        water.image = bpy.data.images.load(str(paths[base]), check_existing=True)
        water.interpolation = 'Closest'
        channels = nodes.new('ShaderNodeSeparateColor')
        links.new(color, channels.inputs['Color'])
        masks = []
        for channel, operation, threshold in [('Red','GREATER_THAN',.78),('Green','LESS_THAN',.31),
                                               ('Blue','GREATER_THAN',.78)]:
            mask = nodes.new('ShaderNodeMath')
            mask.operation = operation
            mask.inputs[1].default_value = threshold
            links.new(channels.outputs[channel], mask.inputs[0])
            masks.append(mask.outputs[0])
        mask = masks[0]
        for other in masks[1:]:
            product = nodes.new('ShaderNodeMath')
            product.operation = 'MULTIPLY'
            links.new(mask, product.inputs[0])
            links.new(other, product.inputs[1])
            mask = product.outputs[0]
        mix = nodes.new('ShaderNodeMixRGB')
        links.new(mask, mix.inputs[0])
        links.new(color, mix.inputs[1])
        links.new(water.outputs['Color'], mix.inputs[2])
        color = mix.outputs[0]
    links.new(color, shader.inputs['Base Color'])
    materials[key] = mat
vertices = [((c-64)*4, (64-r)*4, height[r*128+c]/4) for r in range(128) for c in range(128)]
faces, keys = [], []
for r in range(127):
    for c in range(127):
        key = names[tiles[r*128+c]]
        if key == 'mm5void':
            continue
        i = r*128+c
        faces.extend([(i,i+128,i+1),(i+129,i+1,i+128)])
        keys.extend([key,key])
mesh = bpy.data.meshes.new('MM5 material review native heightfield')
mesh.from_pydata(vertices, [], faces)
for mat in materials.values():
    mesh.materials.append(mat)
indices = {key:i for i,key in enumerate(materials)}
uv = mesh.uv_layers.new()
for i,(poly,key) in enumerate(zip(mesh.polygons,keys)):
    poly.material_index = indices[key]
    points = [(0,1),(0,0),(1,1)] if i%2==0 else [(1,0),(1,1),(0,0)]
    for loop,point in zip(poly.loop_indices,points):
        uv.data[loop].uv = point
object_for('MM5 material review terrain',mesh)
if native:
    points, polygons, coordinates, slots = [], [], [], []
    for model in native['bmodels']:
        for face in model['faces']:
            if face['attributes'] & 0x2000:
                continue
            key = face['texture_name'].lower()
            texture = next(node.image for node in materials[key].node_tree.nodes
                           if node.type == 'TEX_IMAGE')
            polygons.append(tuple(range(len(points), len(points)+len(face['vertex_indices']))))
            points.extend(tuple(model['vertices'][index][axis]/128 for axis in 'xyz')
                          for index in face['vertex_indices'])
            coordinates.extend(((u+face['texture_delta_u'])/texture.size[0],
                                1-(v+face['texture_delta_v'])/texture.size[1])
                               for u,v in zip(face['texture_us'], face['texture_vs']))
            slots.append(indices[key])
    model_mesh = bpy.data.meshes.new('MM5 written native BModels')
    model_mesh.from_pydata(points, [], polygons)
    for mat in materials.values():
        model_mesh.materials.append(mat)
    for face, slot in zip(model_mesh.polygons, slots):
        face.material_index = slot
    model_uv = model_mesh.uv_layers.new(name='Written native UV')
    for loop, coord in zip(model_uv.data, coordinates):
        loop.uv = coord
    object_for('MM5 written native BModels', model_mesh)
else:
    for obj in bpy.data.scenes[globals().get('REVIEW_ARCHITECTURE_SCENE','MM5 Castleview architecture')].objects:
        scene.collection.objects.link(obj)
sun = object_for('MM5 material review sun',bpy.data.lights.new('MM5 material review sun','SUN'))
sun.data.energy = 2.2
sun.rotation_euler = (.5,-.4,-.6)
scene.world = bpy.data.worlds.new('MM5 material review sky')
scene.world.color = (.18,.22,.28)
if globals().get('REVIEW_MAP_LIGHTING', False):
    # Short noon shadows retain roof relief without hiding roads beneath tower shadows.
    sun.rotation_euler = (.15, -.10, -.6)
    sun.data.energy = 1.3
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes['Background']
    background.inputs['Color'].default_value = (.65, .65, .65, 1)
    background.inputs['Strength'].default_value = .8
    # The void is dark presentation space, independent of the ambient lighting used on land.
    nodes, links = scene.world.node_tree.nodes, scene.world.node_tree.links
    void_background = nodes.new('ShaderNodeBackground')
    void_background.inputs['Color'].default_value = (.025, .035, .045, 1)
    light_path = nodes.new('ShaderNodeLightPath')
    mix = nodes.new('ShaderNodeMixShader')
    links.new(light_path.outputs['Is Camera Ray'], mix.inputs[0])
    links.new(background.outputs[0], mix.inputs[1])
    links.new(void_background.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes.get('World Output').inputs['Surface'])
camera = object_for('MM5 material review camera',bpy.data.cameras.new('MM5 material review camera'))
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.render.resolution_x, scene.render.resolution_y = globals().get('REVIEW_RESOLUTION', (1440, 1000))
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'Standard'
views = globals().get('REVIEW_VIEWS', [('acid_oblique',(8000,13000,9000),(0,22500,768),17000),
         ('acid_bank',(2500,17000,2500),(0,22500,768),None),
         ('desert_oblique',(17000,13500,6500),(24000,22000,1400),16000),
         ('scorched_fringe',(4500,29400,3500),(3000,32300,900),6500)])
for name,eye,target,scale in views:
    camera.location = Vector(eye)/128
    camera.rotation_euler = ((0, 0, 0) if eye[:2] == target[:2] else
                            (Vector(target)/128-camera.location).to_track_quat('-Z','Y').to_euler())
    camera.data.type = 'ORTHO' if scale else 'PERSP'
    if scale:
        camera.data.ortho_scale = scale/128
    else:
        camera.data.lens = 35
    camera.data.clip_end = 2000
    scene.render.filepath = str(OUTPUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
if native:
    (OUTPUT/'native_render.json').write_text(json.dumps({
        'nativeSha256': native_digest, 'bmodels': len(native['bmodels']), 'visibleNativeFaces': len(polygons),
        'views': views, 'pixels': [scene.render.resolution_x, scene.render.resolution_y],
        'source': 'Written native ODM vertices, face UVs, terrain and mounted original texture artwork',
        'limits': 'Inspection lighting and static water preview. Native billboards omitted from the top-down bake. '
                  'This rendering does not establish final environment acceptance or runtime minimap alignment.',
    }, indent=2)+'\n')
bpy.context.window.scene = previous
print('Rendered terrain material review; original architecture scene preserved.')
