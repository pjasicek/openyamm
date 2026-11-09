#!/usr/bin/env python3
"""Tier variants (KHR_materials_variants) on a runtime GLB (project folder). Variants eb, s1, s2, s3, s4.
EboraTorso/Head/Legs: eb = the base material (Ebora's paint); s1 = a copy with the siren paint's colour and normal;
s2..s4 = s1 + region mask + ramps (textures/eb_tiers.json). EboraWing: eb = base; s1..s4 = copies with mask + ramps.
Every material: openyamm_specular 0, metallic 0 (as the other MM9 bodies). Args: <in glb> <out glb>"""
import copy, io, json, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, '../claude_shared')
import region_variants as RV
src, dst = sys.argv[1:3]
doc, blob = RV.read_glb(src); blob = bytearray(blob)
cfg = json.load(open('textures/eb_tiers.json')); V = cfg['variants']
def add_image(path, mode='RGB'):
    im = Image.open(path).convert(mode); buf = io.BytesIO(); im.save(buf, 'PNG'); data = buf.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)})
    blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
    doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': 0})
    return len(doc['textures']) - 1
names = [m['name'] for m in doc['materials']]
for m in doc['materials']:
    m.setdefault('extras', {})['openyamm_specular'] = 0.0; m['pbrMetallicRoughness']['metallicFactor'] = 0.0
mapping = {}
for base, short in (('EboraTorso', 'torso'), ('EboraHead', 'head'), ('EboraLegs', 'legs'), ('EboraWing', 'wing')):
    bi = names.index(base); bm = doc['materials'][bi]; entry = cfg['materials'][base]
    mask_tex = add_image('textures/' + entry['mask'], 'RGBA')
    mats = {'eb': bi}
    if short != 'wing':
        s1 = copy.deepcopy(bm); s1['name'] = base + '_S1'
        s1['pbrMetallicRoughness']['baseColorTexture'] = {'index': add_image(f'textures/sr_{short}_tone.png')}
        import os
        nrm = f'textures/sr_{short}_pnormal.png' if short == 'head' and os.path.exists('textures/sr_head_pnormal.png') else f'textures/sr_{short}_normal.png'
        s1['normalTexture'] = {'index': add_image(nrm)}
        doc['materials'].append(s1); mats['s1'] = len(doc['materials']) - 1
    for v in V[1:]:
        if v in mats: continue
        src_m = doc['materials'][mats['s1']] if 's1' in mats else bm
        m = copy.deepcopy(src_m); m['name'] = f'{base}_{v.upper()}'
        m['extras']['openyamm_region_mask'] = {'index': mask_tex}
        m['extras']['openyamm_region_ramps'] = entry['ramps'][v]
        doc['materials'].append(m); mats[v] = len(doc['materials']) - 1
    mapping[bi] = mats
n = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        if prim.get('material') in mapping:
            mats = mapping[prim['material']]
            prim.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [{'material': mats[v], 'variants': [i]} for i, v in enumerate(V)]}
            n += 1
doc.setdefault('extensionsUsed', [])
if 'KHR_materials_variants' not in doc['extensionsUsed']: doc['extensionsUsed'].append('KHR_materials_variants')
doc.setdefault('extensions', {})['KHR_materials_variants'] = {'variants': [{'name': v} for v in V]}
doc, blob = RV._compact(doc, bytes(blob))
RV.write_glb(dst, doc, blob)
print('TIERS', dst, n, 'primitives', len(doc['materials']), 'materials', len(doc['images']), 'images')
