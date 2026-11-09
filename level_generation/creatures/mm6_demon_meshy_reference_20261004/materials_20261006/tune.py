"""Offline demon pigment/roughness touch-up; preserve all geometry, animation and image dimensions."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

stage = Path(__file__).resolve().parent
repo = stage.parents[3]
sys.path.insert(0, str(repo / 'tools'))
from build_actor_lods import read_glb, write_glb
from creature_workspace import project_guard

source = stage.parent / 'expression_20261006'
names = ('Demon_Meshy_Body', 'demon_b_Meshy_Body', 'demon_c_Meshy_Body')
skin_gains = ((1.12, 1.12, 1.12), (.86, 1.18, .76), (1.22, .86, .60))
leather_gains = ((.75, 1.22, .88), (1.26, 1.13, .60), (1.30, .62, .48))


def smooth(values, low, high):
    amount = np.clip((values - low) / (high - low), 0, 1)
    return amount * amount * (3 - 2 * amount)


def image_bytes(document, binary, index):
    view = document['bufferViews'][document['images'][index]['bufferView']]
    offset = view.get('byteOffset', 0)
    return binary[offset:offset + view['byteLength']]


def pixels(content):
    return np.array(Image.open(io.BytesIO(content)).convert('RGBA'))


def png(array):
    stream = io.BytesIO()
    Image.fromarray(array.astype('uint8'), 'RGBA').save(stream, format='PNG')
    return stream.getvalue()


def masks(reference):
    rgb = reference[..., :3] / 255.0
    # Same UVs on A/B/C: the selected A map identifies green leather even when C's leather and skin share a hue.
    green = np.minimum(rgb[..., 1] - rgb[..., 0], rgb[..., 1] - rgb[..., 2])
    leather = smooth(green, .016, .065)
    bone = smooth(rgb.max(axis=2), .31, .58) * (1 - leather)
    return leather, bone


def touch_up(document, binary):
    textures = document['textures']
    materials = document['materials']
    reference_material = next(m for m in materials if m.get('name') == names[0])
    reference_index = textures[reference_material['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    leather, bone = masks(pixels(image_bytes(document, binary, reference_index)))
    skin = 1 - leather - bone
    replacements, summary = {}, {}
    for variant, name in enumerate(names):
        material = next(m for m in materials if m.get('name') == name)
        pbr = material['pbrMetallicRoughness']
        base_index = textures[pbr['baseColorTexture']['index']]['source']
        base = pixels(image_bytes(document, binary, base_index))
        assert base.shape[:2] == leather.shape
        rgb = base[..., :3] / 255.0
        luminance = rgb @ np.array([.2126, .7152, .0722])
        saturation = 1 if variant == 0 else 1.22
        graded = np.maximum(luminance[..., None] + (rgb - luminance[..., None]) * saturation, 0)
        skin_rgb = graded * np.array(skin_gains[variant])
        leather_rgb = rgb * np.array(leather_gains[variant])
        revised = rgb * bone[..., None] + skin_rgb * skin[..., None] + leather_rgb * leather[..., None]
        result = base.copy()
        result[..., :3] = np.round(np.clip(revised, 0, 1) * 255).astype('uint8')
        assert np.array_equal(result[..., 3], base[..., 3])
        replacements[base_index] = png(result)
        (stage / (name + '_base.png')).write_bytes(replacements[base_index])
        material['normalTexture']['scale'] = .75
        rough_index = textures[pbr['metallicRoughnessTexture']['index']]['source']
        rough = pixels(image_bytes(document, binary, rough_index))
        resized_leather = np.asarray(Image.fromarray(leather.astype('float32'), 'F').resize(
            (rough.shape[1], rough.shape[0]), Image.Resampling.BILINEAR))
        resized_bone = np.asarray(Image.fromarray(bone.astype('float32'), 'F').resize(
            (rough.shape[1], rough.shape[0]), Image.Resampling.BILINEAR))
        old = rough[..., 1] / 255.0
        leather_rough = .78 + .10 * old
        bone_rough = .36 + .19 * old
        skin_rough = .66 + .16 * old
        value = bone_rough * resized_bone + leather_rough * resized_leather + skin_rough * (
            1 - resized_bone - resized_leather)
        result = rough.copy()
        result[..., 1] = np.round(value * 255).astype('uint8')
        assert np.array_equal(result[..., [0, 2, 3]], rough[..., [0, 2, 3]])
        replacements[rough_index] = png(result)
        (stage / (name + '_mr.png')).write_bytes(replacements[rough_index])
        Image.fromarray(result[..., 1], 'L').save(stage / (name + '_roughness.png'))
        summary[name] = {'normal_scale': .75, 'roughness_bounds': [float(value.min()), float(value.max())],
                         'skin_rgb_gain': skin_gains[variant], 'leather_rgb_gain': leather_gains[variant]}
    claw = next(m for m in materials if m.get('name') == 'Demon_White_Claws')
    index = textures[claw['pbrMetallicRoughness']['metallicRoughnessTexture']['index']]['source']
    rough = pixels(image_bytes(document, binary, index))
    result = rough.copy()
    result[..., 1] = np.round((.33 + .20 * (rough[..., 1] / 255.0)) * 255).astype('uint8')
    assert np.array_equal(result[..., [0, 2, 3]], rough[..., [0, 2, 3]])
    replacements[index] = png(result)
    (stage / 'Demon_White_Claws_mr.png').write_bytes(replacements[index])
    Image.fromarray(result[..., 1], 'L').save(stage / 'Demon_White_Claws_roughness.png')
    return replacements, summary


def export(filename):
    original, binary = read_glb(source / filename)
    document = copy.deepcopy(original)
    replacements, summary = touch_up(document, binary)
    by_view = {document['images'][i]['bufferView']: content for i, content in replacements.items()}
    payload = bytearray()
    cursor = 0
    for index in sorted(range(len(document['bufferViews'])), key=lambda i: original['bufferViews'][i].get('byteOffset', 0)):
        old = original['bufferViews'][index]
        start, size = old.get('byteOffset', 0), old['byteLength']
        assert start >= cursor, 'Expected disjoint buffer views'
        payload.extend(binary[cursor:start])
        payload.extend(b'\0' * (-len(payload) % 4))
        new = document['bufferViews'][index]
        new['byteOffset'] = len(payload)
        content = by_view.get(index, binary[start:start + size])
        new['byteLength'] = len(content)
        payload.extend(content)
        cursor = start + size
    payload.extend(binary[cursor:])
    for key in ('nodes', 'meshes', 'skins', 'animations', 'accessors', 'images', 'textures', 'samplers', 'extensions'):
        assert document.get(key) == original.get(key), key
    # Covers sparse plume accessors too: every non-image view remains byte-for-byte identical.
    for i, old in enumerate(original['bufferViews']):
        new = document['bufferViews'][i]
        old_content = binary[old.get('byteOffset', 0):old.get('byteOffset', 0) + old['byteLength']]
        new_content = payload[new['byteOffset']:new['byteOffset'] + new['byteLength']]
        if i not in by_view:
            assert new_content == old_content, i
    for i, material in enumerate(original['materials']):
        if material.get('name') in names:
            expected = copy.deepcopy(material)
            expected['normalTexture']['scale'] = .75
            assert document['materials'][i] == expected
        else:
            assert document['materials'][i] == material
    for i, image in enumerate(document['images']):
        before, after = pixels(image_bytes(original, binary, i)), pixels(image_bytes(document, payload, i))
        assert before.shape == after.shape
        if i not in replacements:
            assert image_bytes(original, binary, i) == image_bytes(document, payload, i)
    destination = stage / filename
    write_glb(destination, document, bytes(payload))
    return {'file': filename, 'source_sha256': hashlib.sha256((source / filename).read_bytes()).hexdigest(),
            'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'edited_images': sorted(replacements),
            'geometry_rig_uv_clips_lods_sockets_unchanged': True, 'unchanged_image_sizes': True, 'materials': summary}


if __name__ == '__main__':
    with project_guard(stage.parent, sys.argv[1]):
        report = [export(name) for name in ('mm6_demon_runtime.glb', 'mm6_demon_animated.glb')]
        (stage / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print('Updated existing pigment/roughness images; identical geometry, clips, sockets, LODs and texture dimensions.')
