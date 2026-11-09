#!/usr/bin/env python3
"""Review viewer comparing ooze materials: each tier's GLB with its ramp baked into the base colour (fs_model.sc math)
and the engine's specular as KHR_materials_specular (factor openyamm_specular, texture = the ORM red mask), which three.js
shows. Usage: make_gloss_viewer.py label:glb ...  -> review/viewer/ (index.html and review.js copied from another viewer)."""
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
import region_variants as R  # noqa: E402

VIEWER = HERE / 'review/viewer'
TEMPLATE = HERE.parent / 'mm9_jelly_claude/review/viewer'
TIERS = ['a', 'b', 'c']


def view_bytes(doc, binary, view_index):
    view = doc['bufferViews'][view_index]
    start = view.get('byteOffset', 0)
    return binary[start:start + view['byteLength']]


def named_image(doc, binary, name):
    source = next(entry for entry in doc['images'] if entry.get('name') == name)
    return source, Image.open(io.BytesIO(view_bytes(doc, binary, source['bufferView'])))


def add_image(doc, binary, name, picture):
    out = io.BytesIO()
    picture.save(out, 'PNG')
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(out.getvalue())})
    doc['images'].append({'name': name, 'mimeType': 'image/png', 'bufferView': len(doc['bufferViews']) - 1})
    doc['textures'].append({'sampler': 0, 'source': len(doc['images']) - 1})
    return binary + out.getvalue(), len(doc['textures']) - 1


def bake_tier(doc, binary, material):
    _, base = named_image(doc, binary, 'ooz_a_basecolor_graded')
    _, mask = named_image(doc, binary, 'ooz_region_mask')
    linear = R.srgb_to_linear(np.asarray(base.convert('RGB'), np.float64) / 255)
    weights = np.asarray(mask.convert('RGBA'), np.float64) / 255
    luminance = linear @ R.LUMA
    colour = linear.copy()
    for channel, ramp in enumerate(material['extras']['openyamm_region_ramps']):
        low, high = ramp['range']
        t = np.clip((luminance - low) / (high - low), 0, 1) * 15
        index = np.minimum(np.floor(t).astype(int), 14)
        fraction = (t - index)[..., None]
        stops = np.asarray(ramp['colors'])
        ramped = stops[index] * (1 - fraction) + stops[index + 1] * fraction
        colour = colour * (1 - weights[..., channel:channel + 1]) + ramped * weights[..., channel:channel + 1]
    encoded = np.where(colour <= 0.0031308, colour * 12.92, 1.055 * np.maximum(colour, 0) ** (1 / 2.4) - 0.055)
    return Image.fromarray((np.clip(encoded, 0, 1) * 255).astype(np.uint8))


def viewer_glb(source, tier_index, output):
    doc, binary = read_glb(source)
    material = doc['materials'][0]
    baked = bake_tier(doc, binary, doc['materials'][tier_index])
    binary, base_texture = add_image(doc, binary, 'viewer_base', baked)
    _, orm = named_image(doc, binary, 'ooz_metal_rough_1k')
    orm = orm.convert('RGB')
    specular = Image.merge('RGBA', (*orm.split(), orm.split()[0]))
    binary, specular_texture = add_image(doc, binary, 'viewer_specular', specular)
    material['pbrMetallicRoughness']['baseColorTexture'] = {'index': base_texture}
    material['pbrMetallicRoughness'].pop('metallicFactor', None)
    material['pbrMetallicRoughness']['metallicFactor'] = 0
    material['extensions'] = {'KHR_materials_specular': {'specularFactor': material['extras']['openyamm_specular'],
                                                          'specularTexture': {'index': specular_texture}}}
    material['extras'] = {}
    doc['extensionsUsed'] = sorted(set(doc.get('extensionsUsed', [])) | {'KHR_materials_specular'})
    write_glb(output, doc, binary)


def main():
    VIEWER.mkdir(parents=True, exist_ok=True)
    (VIEWER / 'feedback').mkdir(exist_ok=True)
    (VIEWER / 'feedback/user_feedback.json').write_text('{"findings": []}\n')
    for name in ('index.html', 'review.js'):
        shutil.copy2(TEMPLATE / name, VIEWER / name)
    models = []
    for spec in sys.argv[1:]:
        label, path = spec.split(':', 1)
        for tier_index, tier in enumerate(TIERS):
            model_id = f'{label}_{tier}'
            target = VIEWER / f'{model_id}.glb'
            viewer_glb(Path(path), tier_index, target)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            models.append({'id': model_id, 'label': f'Ooze {tier.upper()} ({label})', 'revision': 'gloss_20261030',
                           'url': f'{model_id}.glb?v={digest[:12]}', 'sha256': digest})
    doc, _ = read_glb(Path(sys.argv[1].split(':', 1)[1]))
    durations = {a['name']: 0.0 for a in doc['animations']}
    for animation in doc['animations']:
        for sampler in animation['samplers']:
            durations[animation['name']] = max(durations[animation['name']], doc['accessors'][sampler['input']]['max'][0])
    clips = {name: {'label': name, 'duration': value, 'mode': 'loop', 'provenance': 'installed mm6_ooz',
                    'anchors': [{'time': 0, 'label': name, 'phase': 'Start', 'source_images': []}]}
             for name, value in sorted(durations.items())}
    manifest = {'revision': 'gloss_20261030', 'model': models[0]['url'].split('?')[0], 'default_clip': 'Standing',
                'default_model': models[0]['id'], 'feedback': 'feedback/user_feedback.json', 'models': models,
                'clips': clips}
    (VIEWER / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
