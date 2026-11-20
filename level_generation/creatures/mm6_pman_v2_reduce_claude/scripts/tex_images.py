#!/usr/bin/env python3
"""Replace the pre-runtime GLB's authoring images (matched by name: pman_{body,head}_{basecolor,normal,metal_rough}_1k)
with this project's composed maps; the old bytes are dropped by rebuilding the buffer. Usage: tex_images.py <glb> (in place)"""
import copy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
path = Path(sys.argv[1]); doc, binary = read_glb(path); binary = bytes(binary)
data = {}
for i, im in enumerate(doc['images']):
    src = P / 'textures' / f"{im['name']}.png"
    assert src.is_file(), im['name']
    data[i] = src.read_bytes()
used = set()
for a in doc['accessors']:
    used.add(a['bufferView'])
packed, views, vmap = bytearray(), [], {}
for old in sorted(used):
    v = copy.deepcopy(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
    packed.extend(b'\0' * (-len(packed) % 4)); v['byteOffset'] = len(packed); packed.extend(binary[start:start + v['byteLength']])
    vmap[old] = len(views); views.append(v)
for a in doc['accessors']:
    a['bufferView'] = vmap[a['bufferView']]
for i, im in enumerate(doc['images']):
    packed.extend(b'\0' * (-len(packed) % 4))
    views.append({'buffer': 0, 'byteOffset': len(packed), 'byteLength': len(data[i])}); packed.extend(data[i])
    im['bufferView'] = len(views) - 1; im['mimeType'] = 'image/png'
doc['bufferViews'] = views
write_glb(path, doc, bytes(packed)); print('IMAGES', [im['name'] for im in doc['images']], f'{len(packed) / 1e6:.1f} MB')
