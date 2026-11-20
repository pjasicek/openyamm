#!/usr/bin/env python3
"""Torso and head per tier: ThrallTorso and ThrallHead primitives of every LOD map each KHR_materials_variants tier to a material with its own base colour and normal (the design differs: tunic, half pelt, bare chest; old bald man, headband, dark hair). Same mesh, UVs, ORM.
Args: <in.glb> <out.glb>"""
import copy, io, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, '../claude_shared')
import region_variants as RV
src, dst = sys.argv[1:3]
doc, blob = RV.read_glb(src); blob = bytearray(blob)
TX = Path('textures')
def add_image(path, name, mode):
    im = Image.open(path).convert(mode); buf = io.BytesIO(); im.save(buf, 'PNG'); data = buf.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)})
    blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    return len(doc['images']) - 1
variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
print('variants', variants)
for name, stem in (('ThrallTorso', 'thrall_torso'), ('ThrallHead', 'thrall_head')):
    base = next(i for i, m in enumerate(doc['materials']) if m['name'] == name)
    bm = doc['materials'][base]
    smp = doc['textures'][bm['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
    bm.setdefault('extras', {}).update({'openyamm_specular': 0.0}); bm['pbrMetallicRoughness']['metallicFactor'] = 0.0
    mats = {}
    for v in variants:
        t = v.split('_')[1]
        if t == 'a': mats[v] = base; continue
        m = copy.deepcopy(bm); m['name'] = f'{name}_{t.upper()}'
        doc['textures'].append({'source': add_image(TX / f'{stem}_{t}_final.png', m['name'], 'RGB'), 'sampler': smp})
        m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
        doc['textures'].append({'source': add_image(TX / f'{stem}_{t}_normal.png', m['name'] + '_n', 'RGB'), 'sampler': smp})
        m['normalTexture'] = {'index': len(doc['textures']) - 1}
        doc['materials'].append(m); mats[v] = len(doc['materials']) - 1
    n = 0
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            if prim.get('material') == base:
                prim.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [{'material': mats[v], 'variants': [i]} for i, v in enumerate(variants)]}
                n += 1
    print('PRIMS', name, n, mats)
RV.write_glb(dst, doc, bytes(blob))
