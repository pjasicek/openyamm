"""Refresh the selected exports without changing geometry, UVs, rig, animation or non-colour maps."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes

WORK = P / 'work/colour_fix'
WORK.mkdir(exist_ok=True)
RAMPS = json.loads((P / 'textures/gloamer_ramps.json').read_text())['materials'][0]['ramps']


def refresh(source, target, far=False):
    doc, binary = read_glb(source)
    before = copy.deepcopy(doc)
    replacements = {}
    for image in doc['images']:
        name = image['name']
        if 'basecolor' not in name:
            continue
        if '_lod' in name:
            if not far:
                continue
            part, _, level, _ = name.split('_')
            primitive = {'GloamerBody': 0, 'GloamerHead': 1, 'GloamerPores': 2}[part]
            path = WORK / f'{level}_p{primitive}_basecolor.png'
        else:
            path = P / 'textures' / (name.replace('_throatsac', '') + '.png')
        replacements[image['bufferView']] = path.read_bytes()
    for material in doc['materials']:
        extras = material.get('extras', {})
        if 'openyamm_region_ramps' in extras:
            tier = material['name'].split('_')[1].lower()
            extras['openyamm_region_ramps'] = RAMPS['gloamer_' + tier]
    packed = bytearray()
    for index, view in enumerate(doc['bufferViews']):
        start = view.get('byteOffset', 0)
        data = replacements.get(index, binary[start:start + view['byteLength']])
        packed.extend(b'\0' * (-len(packed) % 4))
        view['byteOffset'], view['byteLength'] = len(packed), len(data)
        packed.extend(data)
    # Every vertex, index, UV, skin weight and motion key must survive byte-for-byte.
    assert all(accessor_bytes(before, binary, i) == accessor_bytes(doc, packed, i)
               for i in range(len(doc['accessors'])))
    for key in before.keys() - {'buffers', 'bufferViews', 'materials'}:
        assert before[key] == doc[key], key
    for old, new in zip(before['materials'], doc['materials']):
        old.get('extras', {}).pop('openyamm_region_ramps', None)
        check = copy.deepcopy(new)
        check.get('extras', {}).pop('openyamm_region_ramps', None)
        assert old == check
    write_glb(target, doc, packed)
    return {'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'basecolor_images_replaced': len(replacements),
            'unchanged_accessors': len(doc['accessors']), 'geometry_rig_animation_unchanged': True}


crop = json.loads((P / 'review/sac_texture_crop.json').read_text())['crop_xywh']
x, y, w, h = crop
Image.open(P / 'textures/gloamer_head_basecolor_1k.png').crop((x, y, x + w, y + h)).save(
    P / 'textures/gloamer_sac_basecolor_256.png')
# Far LODs have their own UVs. Reuse their existing unwrap and the established surface transfer.
for level in (2, 3):
    shutil.copy2(P / f'work/lodrep/bake_r25_12/lod{level}.npz', WORK / f'lod{level}.npz')
refresh(P / 'work/lodrep/r25_12.built.glb', WORK / 'built.glb')
subprocess.run([sys.executable, str(P.parent / 'lod_repair_claude/scripts/transfer_textures.py'),
                str(WORK / 'built.glb'), 'Gloamer', str(WORK)], check=True)
report = {}
for name in ('hes_gloamer', 'hes_gloamer_sac'):
    report[name] = refresh(P / f'export/{name}.glb', P / f'export/{name}.glb', far=True)
(P / 'review/colour_fix/validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
