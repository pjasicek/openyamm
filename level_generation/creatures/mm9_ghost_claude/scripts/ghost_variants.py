#!/usr/bin/env python3
"""Tier materials: ghost_a, ghost_b, ghost_c on the four primitives. Body materials: B keeps the paint, A and C carry the shared mask + their ramps. Head: one head colour per identity (the face is
a different painting per tier, which a ramp cannot be; shares normal and ORM). alpha per tier in baseColorFactor. All blended, single-sided.
Usage: ghost_variants.py in.glb out.glb"""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
T = Path('textures')
ALPHA = {'ghost_a': 0.8, 'ghost_b': 1.0, 'ghost_c': 1.0}
GLOW = {}
src, dst = sys.argv[1:3]
doc, binary = RV.read_glb(src)
binary = bytearray(binary)
R = json.load(open(T / 'ghost_ramps.json'))
names = [m.get('name', '') for m in doc['materials']]


def add_image(path, stem):
    global binary
    data = Path(path).read_bytes()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary += data
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': stem})
    tex = {'source': len(doc['images']) - 1}
    base = doc['materials'][names.index('Ghost')]['pbrMetallicRoughness']['baseColorTexture']
    if 'sampler' in doc['textures'][base['index']]:
        tex['sampler'] = doc['textures'][base['index']]['sampler']
    doc['textures'].append(tex)
    return len(doc['textures']) - 1


mask = add_image(T / 'ghost_region_mask.png', 'ghost_region_mask')
heads = {'ghost_a': add_image(T / 'ghost_head_a_rgba.png', 'ghost_head_a'), 'ghost_b': add_image(T / 'ghost_head_b_rgba.png', 'ghost_head_b'),
         'ghost_c': add_image(T / 'ghost_head_c_rgba.png', 'ghost_head_c')}
variants = ['ghost_a', 'ghost_b', 'ghost_c']
replaced = {}
for name in ('Ghost', 'GhostArmL', 'GhostArmR', 'GhostHead'):
    base = next(i for i, n in enumerate(names) if n == name or n.startswith(name + '.'))
    copies = []
    for v in variants:
        m = copy.deepcopy(doc['materials'][base])
        m['name'] = f"{name}_{v.split('_')[-1].upper()}"
        m['alphaMode'] = 'BLEND'; m.pop('alphaCutoff', None); m['doubleSided'] = False
        pbr = m.setdefault('pbrMetallicRoughness', {})
        pbr['metallicFactor'] = 0
        pbr['baseColorFactor'] = [1, 1, 1, ALPHA[v]]
        ex = m.setdefault('extras', {})
        ex['openyamm_specular'] = 0
        ex['openyamm_edge_darkening'] = 0.0
        if name == 'GhostHead':
            pbr['baseColorTexture'] = {'index': heads[v]}
        elif v in R:
            ex['openyamm_region_mask'] = {'index': mask}
            ex['openyamm_region_ramps'] = R[v]
        doc['materials'].append(m); copies.append(len(doc['materials']) - 1)
    replaced[base] = copies
mapped = 0
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        c = replaced.get(p.get('material'))
        if c is None:
            continue
        p['material'] = c[0]
        p.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [{'material': c[i], 'variants': [i]} for i in range(3)]}
        mapped += 1
doc.setdefault('extensionsUsed', [])
if 'KHR_materials_variants' not in doc['extensionsUsed']:
    doc['extensionsUsed'].append('KHR_materials_variants')
doc.setdefault('extensions', {})['KHR_materials_variants'] = {'variants': [{'name': n} for n in variants]}
doc, binary = RV._compact(doc, bytes(binary))
RV.write_glb(dst, doc, binary)
print('VARIANTS', mapped, 'primitives', len(doc['materials']), 'materials', len(doc['images']), 'images')
