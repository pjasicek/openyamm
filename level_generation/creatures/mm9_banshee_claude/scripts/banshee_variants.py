#!/usr/bin/env python3
"""Tier materials banshee_a, _b, _c (Fright, Dread, Terror) on the ten primitives. Body parts and the dress share one paint (the ribbed skin E's) and recolour by mask + ramps; the Fright's flat ramp in the bodice region is how its ribs vanish. The cloak has no ramps (MM9's skins share it). Hair: a swatch + ramps.
Head: one 1K colour per identity (a woman, a rotting skull, a clean skull: paintings, which a ramp cannot be; normal and ORM shared). alpha per tier in baseColorFactor. All blended and single-sided except the head, which is opaque: a blended head has no depth, so lips, teeth, mouth walls, creases and a hand before the face drew in fixed triangle order; opaque it is drawn right from every angle, and everything blended is depth tested against it. The neck stays blended and fades from opaque to the torso.
Usage: banshee_variants.py in.glb out.glb"""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
T = Path('textures')
ALPHA = {'banshee_a': 1.0, 'banshee_b': 0.94, 'banshee_c': 0.88}
src, dst = sys.argv[1:3]
doc, binary = RV.read_glb(src)
binary = bytearray(binary)
R = json.load(open(T / 'banshee_ramps.json'))
names = [m.get('name', '') for m in doc['materials']]


def add_image(path, stem):
    global binary
    data = Path(path).read_bytes()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary += data
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': stem})
    tex = {'source': len(doc['images']) - 1}
    base = doc['materials'][names.index('Banshee')]['pbrMetallicRoughness']['baseColorTexture']
    if 'sampler' in doc['textures'][base['index']]:
        tex['sampler'] = doc['textures'][base['index']]['sampler']
    doc['textures'].append(tex)
    return len(doc['textures']) - 1


mask = add_image(T / 'banshee_region_mask.png', 'banshee_region_mask')
hmask = add_image(T / 'banshee_hair_mask.png', 'banshee_hair_mask')
heads = {'banshee_a': add_image(T / 'banshee_head_a_rgba.png', 'banshee_head_a'), 'banshee_b': add_image(T / 'banshee_head_b_rgba.png', 'banshee_head_b'),
         'banshee_c': add_image(T / 'banshee_head_c_rgba.png', 'banshee_head_c')}
variants = ['banshee_a', 'banshee_b', 'banshee_c']
replaced = {}
ROLE = {'Banshee': 'body', 'BansheeArmL': 'body', 'BansheeArmR': 'body', 'BansheeSkirt': 'skirt', 'BansheeCape': 'cloth', 'BansheeWingL': 'cloth', 'BansheeWingR': 'cloth', 'BansheeHead': 'head', 'BansheeHairL': 'hair', 'BansheeHairR': 'hair', 'BansheeNeck': 'neck'}
for name, role in ROLE.items():
    base = next(i for i, n in enumerate(names) if n == name or n.startswith(name + '.'))
    copies = []
    for v in variants:
        m = copy.deepcopy(doc['materials'][base])
        m['name'] = f"{name}_{v.split('_')[-1].upper()}"
        m['alphaMode'] = 'OPAQUE' if role == 'head' else 'BLEND'; m.pop('alphaCutoff', None); m['doubleSided'] = False
        pbr = m.setdefault('pbrMetallicRoughness', {})
        pbr['metallicFactor'] = 0
        pbr['baseColorFactor'] = [1, 1, 1, 1.0 if role in ('head', 'neck') else ALPHA[v]]
        ex = m.setdefault('extras', {})
        ex['openyamm_specular'] = 0
        ex['openyamm_edge_darkening'] = 0.0
        if role in ('head', 'neck'):
            pbr['baseColorTexture'] = {'index': heads[v]}
        elif role in ('body', 'skirt') and v in R[role]:
            ex['openyamm_region_mask'] = {'index': mask}
            ex['openyamm_region_ramps'] = R[role][v]
        elif role == 'hair':
            ex['openyamm_region_mask'] = {'index': hmask}
            ex['openyamm_region_ramps'] = R['hair'][v]
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
