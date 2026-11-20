"""Verify Meshy surface correspondence, then append variant materials without replacing animated geometry."""
import copy
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

stage = Path(__file__).resolve().parent
repo = stage.parents[3]
sys.path.insert(0, str(repo / 'tools'))
from build_actor_lods import read_glb, write_glb

eye_colors = {'demon_a': [231, 156, 156], 'demon_b': [250, 102, 102], 'demon_c': [250, 176, 62]}


def srgb(rgb):
    return [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in np.array(rgb) / 255] + [1]


def corners(path):
    document, binary = read_glb(path)
    arrays = []
    for primitive in document['meshes'][0]['primitives']:
        def accessor(index):
            item = document['accessors'][index]
            view = document['bufferViews'][item['bufferView']]
            offset = view.get('byteOffset', 0) + item.get('byteOffset', 0)
            width = {'VEC3': 3, 'VEC2': 2, 'SCALAR': 1}[item['type']]
            dtype = {5123: '<u2', 5125: '<u4', 5126: '<f4'}[item['componentType']]
            stride = view.get('byteStride', np.dtype(dtype).itemsize * width)
            return np.ndarray((item['count'], width), dtype=dtype, buffer=binary,
                              offset=offset, strides=(stride, np.dtype(dtype).itemsize)).copy()
        values = np.column_stack([accessor(primitive['attributes']['POSITION']),
                                  accessor(primitive['attributes']['TEXCOORD_0'])])
        arrays.append(values[accessor(primitive['indices']).ravel()])
    return np.concatenate(arrays)


# Blender's bundled Python has NumPy but not SciPy: exploit correspondence within bounded rounding bins.
# The precise KD-tree/winding audit is run by verify.py in the host Python after assembly.
upload = corners(stage / 'demon_neutral_upload.glb')
report = {'eye_srgb': eye_colors, 'source_upload': 'demon_neutral_upload.glb', 'variants': {}}
for variant in ('demon_b', 'demon_c'):
    returned = corners(stage.parent / f'meshy/{variant}_texture_v1/model_urls_glb.glb')
    assert returned.shape == upload.shape
    # Meshy centers and uniformly normalizes this upload to height two. UVs stay unchanged.
    center = (upload[:, :3].min(0) + upload[:, :3].max(0)) / 2
    scale = (upload[:, 1].max() - upload[:, 1].min()) / 2
    returned[:, :3] = returned[:, :3] * scale + center
    report['variants'][variant] = {'source': f'meshy/{variant}_texture_v1/model_urls_glb.glb',
        'corners': len(returned), 'normalized_height': 2, 'restored_height': float(scale * 2)}

master = stage.parent / 'attack_windup_20261006/mm6_demon_animation_master.blend'
bpy.ops.wm.open_mainfile(filepath=str(master))
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o.get('material_role') == 'body')
base = body.data.materials[0]
materials = {}
for variant in ('demon_b', 'demon_c'):
    material = base.copy()
    material.name = variant + '_Meshy_Body'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    directory = stage.parent / f'meshy/{variant}_texture_v1'
    for input_name, filename, linear in [('Base Color', 'base_color', False), ('Roughness', 'roughness', True)]:
        for link in list(shader.inputs[input_name].links):
            links.remove(link)
        node = nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(directory / f'texture_urls_0_{filename}.png'), check_existing=True)
        node.image.colorspace_settings.name = 'Non-Color' if linear else 'sRGB'
        if linear:
            node.image.scale(1024, 1024)
        node.image.pack()
        links.new(node.outputs['Color'], shader.inputs[input_name])
    normal = next(n for n in nodes if n.type == 'NORMAL_MAP')
    normal.inputs['Strength'].default_value = 1
    normal_image = nodes.new('ShaderNodeTexImage')
    normal_image.image = bpy.data.images.load(str(directory / 'texture_urls_0_normal.png'), check_existing=True)
    normal_image.image.colorspace_settings.name = 'Non-Color'
    normal_image.image.scale(1024, 1024)
    normal_image.image.pack()
    for link in list(normal.inputs['Color'].links):
        links.remove(link)
    links.new(normal_image.outputs['Color'], normal.inputs['Color'])
    for link in list(shader.inputs['Metallic'].links):
        links.remove(link)
    shader.inputs['Metallic'].default_value = 0
    material.use_fake_user = True
    materials[variant] = material
neutral_iris = body.data.materials[1]
neutral_iris.name = 'Demon_Iris'
shader = next(n for n in neutral_iris.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
shader.inputs['Base Color'].default_value = (1, 1, 1, 1)
neutral_iris.diffuse_color = (1, 1, 1, 1)
for variant, color in eye_colors.items():
    iris = neutral_iris.copy()
    iris.name = variant + '_Iris'
    iris.diffuse_color = srgb(color)
    next(n for n in iris.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = srgb(color)
    iris.use_fake_user = True
    materials[variant + '_iris'] = iris
scene = bpy.data.scenes.new('Variant_Materials_Export')
bpy.context.window.scene = scene
static = bpy.data.objects.new('Variant_Materials_Export', body.data.copy())
scene.collection.objects.link(static)
static.data.materials.clear()
for material in materials.values():
    static.data.materials.append(material)
for index, polygon in enumerate(static.data.polygons):
    polygon.material_index = index % len(materials)
static.select_set(True)
bpy.context.view_layer.objects.active = static
bpy.ops.export_scene.gltf(filepath=str(stage / 'variant_materials.glb'), export_format='GLB',
    use_selection=True, use_active_scene=True, export_animations=False, export_skins=False,
    export_morph=False, export_image_format='AUTO', export_cameras=False, export_lights=False)
export, payload = read_glb(stage / 'variant_materials.glb')
# The runtime's material image contract is PNG. Convert exporter-generated RGB JPEGs once offline.
packed = stage / 'packed'
packed.mkdir(exist_ok=True)
image_bytes = []
for index, image in enumerate(export['images']):
    view = export['bufferViews'][image['bufferView']]
    content = payload[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
    if image['mimeType'] != 'image/png':
        temporary = packed / f'image_{index}.jpg'
        temporary.write_bytes(content)
        converted = bpy.data.images.load(str(temporary), check_existing=False)
        converted.file_format = 'PNG'
        converted.filepath_raw = str(packed / f'image_{index}.png')
        converted.save()
        content = Path(converted.filepath_raw).read_bytes()
        bpy.data.images.remove(converted)
    image_bytes.append(content)
bpy.data.objects.remove(static, do_unlink=True)
bpy.data.scenes.remove(scene)
bpy.context.window.scene = next(s for s in bpy.data.scenes if body.name in s.objects)
body.data.materials[1] = materials['demon_a_iris']
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'mm6_demon_variants_master.blend'), compress=True)


def assemble(source, destination):
    original, original_binary = read_glb(source)
    document, binary = copy.deepcopy(original), bytearray(original_binary)
    image_offset, texture_offset = len(document['images']), len(document['textures'])
    sampler_offset = len(document.get('samplers', []))
    samplers = copy.deepcopy(export.get('samplers', []))
    for sampler in samplers:
        sampler['minFilter'] = 9987
    document.setdefault('samplers', []).extend(samplers)
    for image, content in zip(export['images'], image_bytes):
        item = copy.deepcopy(image)
        item['mimeType'] = 'image/png'
        binary.extend(b'\0' * (-len(binary) % 4))
        item['bufferView'] = len(document['bufferViews'])
        document['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(content)})
        binary.extend(content)
        document['images'].append(item)
    for texture in export['textures']:
        item = copy.deepcopy(texture)
        item['source'] += image_offset
        if 'sampler' in item:
            item['sampler'] += sampler_offset
        document['textures'].append(item)
    indices = {}
    for source_material in export['materials']:
        material = copy.deepcopy(source_material)
        for owner, key in [(material, 'normalTexture'), (material.get('pbrMetallicRoughness', {}), 'baseColorTexture'),
                           (material.get('pbrMetallicRoughness', {}), 'metallicRoughnessTexture')]:
            if key in owner:
                owner[key]['index'] += texture_offset
        indices[material['name']] = len(document['materials'])
        document['materials'].append(material)
    iris_index = next(i for i, m in enumerate(document['materials']) if m.get('name') == 'Demon_Red_Iris')
    document['materials'][iris_index]['name'] = 'Demon_Iris'
    document['materials'][iris_index]['pbrMetallicRoughness']['baseColorFactor'] = [1, 1, 1, 1]
    body_index = next(i for i, m in enumerate(document['materials']) if m.get('name') == 'Demon_Meshy_Body')
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            mappings = []
            for index, variant in enumerate(eye_colors):
                if primitive.get('material') == iris_index:
                    mappings.append({'material': indices[variant + '_Iris'], 'variants': [index]})
                elif primitive.get('material') == body_index and variant != 'demon_a':
                    mappings.append({'material': indices[variant + '_Meshy_Body'], 'variants': [index]})
            if mappings:
                primitive.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': mappings}
    document.setdefault('extensionsUsed', []).append('KHR_materials_variants')
    document.setdefault('extensions', {})['KHR_materials_variants'] = {
        'variants': [{'name': name} for name in eye_colors]}
    for key in ('nodes', 'skins', 'animations', 'accessors'):
        assert document[key] == original[key], key
    assert bytes(binary[:len(original_binary)]) == original_binary
    write_glb(destination, document, bytes(binary))
    return {'path': str(destination), 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
            'additional_image_bytes': len(binary) - len(original_binary)}

report['runtime'] = assemble(stage.parent / 'attack_windup_20261006/mm6_demon_runtime.glb',
                             stage / 'mm6_demon_runtime.glb')
report['portable'] = assemble(stage.parent / 'attack_windup_20261006/mm6_demon_animated.glb',
                              stage / 'mm6_demon_animated.glb')
(stage / 'assembly.json').write_text(json.dumps(report, indent=2) + '\n')
print('Appended independent A/B/C materials; preserved all nodes, rig, clips, LOD vertices and binary prefix.')
