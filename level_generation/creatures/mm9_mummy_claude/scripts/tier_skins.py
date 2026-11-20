#!/usr/bin/env python3
"""Tier materials: variants mummy_a/b/c. A keeps the GLB's textures; B and C get their own base colour and normal for body and head (the tiers differ in pattern and face: Canopic fully wrapped, bearded man;
Embalmed torn open, skull; Petrified criss-crossed over dark flesh), and share A's sampler; ORM own too (roughness follows the paint). Args: <in> <out>"""
import json, struct, sys
from pathlib import Path
IN, OUT = sys.argv[1:3]
raw = open(IN, 'rb').read()
n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n]); blob = bytearray(raw[28 + n:])
mats = doc['materials']
base = {m['name']: i for i, m in enumerate(mats)}
print('materials', list(base))
BODY, HEAD = next(i for k, i in base.items() if k.startswith('MummyHead')), None
BODY, HEAD = base['Mummy'], base['MummyHead']
def addimg(path):
    data = Path(path).read_bytes()
    while len(blob) % 4: blob.append(0)
    o = len(blob); blob.extend(data)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': o, 'byteLength': len(data)})
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
    doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': 0})
    return len(doc['textures']) - 1
def copy_mat(i, name, b, nrm, orm=None):
    m = json.loads(json.dumps(mats[i])); m['name'] = name
    m['pbrMetallicRoughness']['baseColorTexture']['index'] = addimg(b)
    m['normalTexture']['index'] = addimg(nrm)
    # ORM stays A's: AO is the mesh's, roughness is unused with specular off, so nothing per tier here
    mats.append(m); return len(mats) - 1
tb = {}
for t in 'BC':
    tb[t] = (copy_mat(BODY, f'Mummy_{t}', f'textures/mummy_{t}_base_final.png', f'textures/mummy_{t}_normal_linen_1k.png'),
             copy_mat(HEAD, f'MummyHead_{t}', f'textures/head_{t}_final.png', f'textures/head_{t}_normal_1k.png'))
for i in (BODY, HEAD):
    mats[i].setdefault('extras', {})
for m in mats:
    m.setdefault('extras', {})['openyamm_specular'] = 0.0
    m['pbrMetallicRoughness']['metallicFactor'] = 0
# colour-only tier differences stay out of the images: a factor per material, towards MM9's darker skins
FACT = {'Mummy': .85, 'MummyHead': .90, 'Mummy_B': .95, 'MummyHead_B': .90, 'Mummy_C': .60, 'MummyHead_C': .80}
for m in mats:
    f = FACT[m['name']]; m['pbrMetallicRoughness']['baseColorFactor'] = [f, f, f, 1.0]
cnt = 0
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        if 'material' not in p: continue
        k = p['material']
        if k not in (BODY, HEAD): continue
        col = 0 if k == BODY else 1
        p.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [{'material': k, 'variants': [0]}, {'material': tb['B'][col], 'variants': [1]}, {'material': tb['C'][col], 'variants': [2]}]}
        cnt += 1
doc.setdefault('extensionsUsed', [])
if 'KHR_materials_variants' not in doc['extensionsUsed']: doc['extensionsUsed'].append('KHR_materials_variants')
doc.setdefault('extensions', {})['KHR_materials_variants'] = {'variants': [{'name': 'mummy_a'}, {'name': 'mummy_b'}, {'name': 'mummy_c'}]}
while len(blob) % 4: blob.append(0)
doc['buffers'][0]['byteLength'] = len(blob)
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(j) + len(blob))); f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j)
    f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
print('tiers on', cnt, 'primitives,', len(doc['images']), 'images')
