#!/usr/bin/env python3
"""The torso part per tier: the ZombieTorso primitive of every LOD maps each KHR_materials_variants tier to its own material with its own base colour and normal (the design differs: bare chest, vest, mail).
Same mesh, same UVs, same ORM. Args: <in.glb> <out.glb>"""
import copy, io, json, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, '../claude_shared')
import region_variants as RV
src, dst = sys.argv[1:3]
doc, blob = RV.read_glb(src)
blob = bytearray(blob)
TX = Path('textures')


def add_image(path, name, mode):
    im = Image.open(path).convert(mode)
    buf = io.BytesIO(); im.save(buf, 'PNG'); data = buf.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)})
    blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    return len(doc['images']) - 1


base = next(i for i, m in enumerate(doc['materials']) if m['name'] == 'ZombieTorso')
bm = doc['materials'][base]
variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
print('variants', variants)
smp = doc['textures'][bm['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
bm.setdefault('extras', {}).update({'openyamm_specular': 0.0}); bm['pbrMetallicRoughness']['metallicFactor'] = 0.0
mats = {}
for v in variants:
    t = v.split('_')[1]
    if t == 'a':
        mats[v] = base; continue
    m = copy.deepcopy(bm); m['name'] = f'ZombieTorso_{t.upper()}'
    doc['textures'].append({'source': add_image(TX / f'zombie_torso_{t}_final.png', m['name'], 'RGB'), 'sampler': smp})
    m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    doc['textures'].append({'source': add_image(TX / f'zombie_torso_{t}_normal.png', m['name'] + '_n', 'RGB'), 'sampler': smp})
    m['normalTexture'] = {'index': len(doc['textures']) - 1}
    doc['materials'].append(m); mats[v] = len(doc['materials']) - 1
n = 0
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        if prim.get('material') == base:
            ext = prim.setdefault('extensions', {})
            ext['KHR_materials_variants'] = {'mappings': [{'material': mats[v], 'variants': [i]} for i, v in enumerate(variants)]}
            n += 1
print('TORSO primitives mapped', n, 'materials', mats)
RV.write_glb(dst, doc, bytes(blob))
