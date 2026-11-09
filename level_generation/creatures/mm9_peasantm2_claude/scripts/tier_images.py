#!/usr/bin/env python3
"""Tier images ramps cannot give: torso (doublet, mantle, sleeves, shin bands) and head differ in design per tier (README, deviation). Shared ORM per set. Args: <in glb> <out glb>"""
import copy, io, json, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, '../claude_shared')
import region_variants as RV
src, dst = sys.argv[1:3]
doc, blob = RV.read_glb(src); blob = bytearray(blob)
def add_image(path, mode='RGB'):
    im = Image.open(path).convert(mode); buf = io.BytesIO(); im.save(buf, 'PNG'); data = buf.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)})
    blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
    return len(doc['images']) - 1
variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
names = [m['name'] for m in doc['materials']]; print('materials', names, 'variants', variants)
for mn, stem in (('NbTorso', 'nb_torso'), ('NbHead', 'nb_head')):
    hi = names.index(mn); hm = doc['materials'][hi]
    hm.setdefault('extras', {})['openyamm_specular'] = 0.0; hm['pbrMetallicRoughness']['metallicFactor'] = 0.0
    smp = doc['textures'][hm['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
    mats = {}
    for v in variants:
        t = v[-1]
        if t == 'a': mats[v] = hi; continue
        m = copy.deepcopy(hm); m['name'] = f'{mn}_{t.upper()}'
        doc['textures'].append({'source': add_image(f'textures/{stem}_{t}_final.png'), 'sampler': smp})
        m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
        doc['textures'].append({'source': add_image(f'textures/{stem}_{t}_normal2.png'), 'sampler': smp})
        m['normalTexture'] = {'index': len(doc['textures']) - 1}
        doc['materials'].append(m); mats[v] = len(doc['materials']) - 1
    n = 0
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            if prim.get('material') == hi:
                prim.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [{'material': mats[v], 'variants': [i]} for i, v in enumerate(variants)]}; n += 1
    print(mn, 'prims', n)
RV.write_glb(dst, doc, bytes(blob))
print('tier images', dst, len(doc['images']), 'images', round(len(blob) / 1e6, 1), 'MB')
