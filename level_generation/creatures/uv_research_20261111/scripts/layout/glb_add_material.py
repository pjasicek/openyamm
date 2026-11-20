#!/usr/bin/env python3
"""Give every primitive of a GLB one material with a 2048 placeholder base-colour PNG, so texture_quality.py measures
it (the Blender exporter dropped the material on imported installed creatures).

    glb_add_material.py <in glb> <out glb> [--size 2048]
"""
import argparse
import io
import json
import struct
from pathlib import Path

from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('inp')
parser.add_argument('out')
parser.add_argument('--size', type=int, default=2048)
args = parser.parse_args()
raw = Path(args.inp).read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n])
binary = bytearray(raw[28 + n:28 + n + struct.unpack_from('<I', raw, 20 + n)[0]])
buf = io.BytesIO()
Image.new('L', (args.size, args.size), 128).save(buf, 'PNG')
png = buf.getvalue()
while len(binary) % 4:
    binary.append(0)
offset = len(binary)
binary += png
while len(binary) % 4:
    binary.append(0)
doc.setdefault('bufferViews', []).append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(png)})
doc['images'] = [{'name': 'placeholder', 'mimeType': 'image/png', 'bufferView': len(doc['bufferViews']) - 1}]
doc['textures'] = [{'source': 0}]
doc['materials'] = [{'name': 'measure', 'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}}}]
doc.pop('samplers', None)
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        prim['material'] = 0
doc['buffers'] = [{'byteLength': len(binary)}]
js = json.dumps(doc).encode()
while len(js) % 4:
    js += b' '
out = struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binary))
out += struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(binary), 0x004E4942) + bytes(binary)
Path(args.out).write_bytes(out)
