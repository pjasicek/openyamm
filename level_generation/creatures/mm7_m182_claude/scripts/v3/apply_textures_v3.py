#!/usr/bin/env python3
"""Swap the v3 maps (textures/v3/m182v3_*: base colour, normal, specular/roughness, region mask), the three burn maps
(textures/v3/m182v3_*_burn.png) and the v3 ramps into a dragon GLB whose LOD0 already carries the v3 geometry and
UVs (swap_lod0.py output). Images are replaced in place (the tier materials share them); the variants become
m182_a / m182_b / m182_c (MM7 skins); unreferenced buffer data is compacted. Usage: apply_textures_v3.py <in> <out>"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[2]; T = P / 'textures/v3'
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = R.read_glb(src); binary = bytearray(binary)
mats = {m['name']: m for m in doc['materials']}
ramps = json.loads((T / 'm182v3_ramps.json').read_text())


def replace(tex_index, path):
    data = Path(path).read_bytes(); img = doc['textures'][tex_index]['source']
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    doc['images'][img] = {'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(path).stem}


done = set()
for label in ['body', 'head', 'wings']:
    m = mats[f'Dragon{label.title()}_A']
    slots = {'burn': (m['extras']['openyamm_burn_map']['index'], T / f'm182v3_{label}_burn.png'),
             'base': (m['pbrMetallicRoughness']['baseColorTexture']['index'], T / f'm182v3_{label}_basecolor_2k.png'),
             'mr': (m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'], T / f'm182v3_{label}_metal_rough_2k.png'),
             'normal': (m['normalTexture']['index'], T / f'm182v3_{label}_normal_2k.png'),
             'mask': (m['extras']['openyamm_region_mask']['index'], T / f'm182v3_{label}_region_mask.png')}
    for key, (tex, path) in slots.items():
        assert tex not in done, (label, key)
        replace(tex, path); done.add(tex)
for name, rr in ramps.items():
    mats[name]['extras']['openyamm_region_ramps'] = rr
doc['extensions']['KHR_materials_variants']['variants'] = [{'name': 'm182_a'}, {'name': 'm182_b'}, {'name': 'm182_c'}]
doc, binary = R._compact(doc, bytes(binary))
R.write_glb(dst, doc, binary)
print('APPLIED', len(done), 'images,', len(ramps), 'ramp sets ->', dst, f'{len(binary) / 1e6:.1f} MB')
