#!/usr/bin/env python3
"""Tier C keeps its own colour and normal images (body and head set): the Gnoll wears stitched leather, a ramp cannot make that; ORM shared. Materials Trog_C, TrogHead_C lose their ramps and take the images. Normal maps flipped to +y up as prepare_actor_glb did for the others. Args: <in> <out>"""
import json, struct, sys, io
from pathlib import Path
from PIL import Image
import numpy as np
IN, OUT = sys.argv[1:3]
raw = open(IN, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n]); blob = bytearray(raw[28 + n:])
def addimg(data, name):
    while len(blob) % 4: blob.append(0)
    o = len(blob); blob.extend(data); doc['bufferViews'].append({'buffer': 0, 'byteOffset': o, 'byteLength': len(data)})
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': 0}); return len(doc['textures']) - 1
def png(path, flip=False):
    im = Image.open(path).convert('RGB')
    if flip:
        a = np.asarray(im).copy(); a[..., 1] = 255 - a[..., 1]; im = Image.fromarray(a)
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True); return b.getvalue()
SET = {'Trog_C': ('textures/body_c_final.png', 'textures/body_c_normal_1k.png'), 'TrogHead_C': ('textures/head_c_final.png', 'textures/head_c_normal_1k.png')}
for m in doc['materials']:
    if m['name'] in SET:
        b, nr = SET[m['name']]
        m['pbrMetallicRoughness']['baseColorTexture'] = {'index': addimg(png(b), Path(b).stem)}
        m['normalTexture'] = {'index': addimg(png(nr, True), Path(nr).stem)}
        ex = m.get('extras', {})
        for k in ('openyamm_region_mask', 'openyamm_region_ramps'): ex.pop(k, None)
print('materials', [(m['name'], sorted(m.get('extras', {}))) for m in doc['materials']])
while len(blob) % 4: blob.append(0)
doc['buffers'][0]['byteLength'] = len(blob)
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(j) + len(blob))); f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j)
    f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
