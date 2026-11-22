#!/usr/bin/env python3
"""Black basalt copies of installed MM6 rock decorations (lane S, D-40: X7's Dragon Tower crag). The mesh, UVs, normal
and roughness maps stay; the base colour becomes near-black blue-grey basalt with the source's own light and dark
detail (luminance mapped onto a basalt ramp, contrast raised a little).
Usage: basalt.py <source.glb> <out.glb>"""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
raw = src.read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n])
rest = raw[20 + n:]
binary = bytearray(rest[8:8 + struct.unpack_from('<I', rest, 0)[0]])
LOW, HIGH = np.array([0.010, 0.011, 0.014]), np.array([0.105, 0.108, 0.122])   # linear basalt ramp


def srgb_to_linear(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(v):
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)


colour_images = {doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
                 for m in doc['materials'] if 'baseColorTexture' in m.get('pbrMetallicRoughness', {})}
new_views = {}
for index in colour_images:
    view = doc['bufferViews'][doc['images'][index]['bufferView']]
    start = view.get('byteOffset', 0)
    image = Image.open(io.BytesIO(bytes(binary[start:start + view['byteLength']]))).convert('RGBA')
    rgba = np.asarray(image, float) / 255
    lum = srgb_to_linear(rgba[..., :3]) @ np.array([0.2126, 0.7152, 0.0722])
    lo, hi = np.percentile(lum, [2, 98])
    t = np.clip((lum - lo) / max(hi - lo, 1e-4), 0, 1) ** 1.15
    colour = LOW + (HIGH - LOW) * t[..., None]
    out = np.dstack([linear_to_srgb(colour), rgba[..., 3:]])
    buffer = io.BytesIO()
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(buffer, 'PNG')
    new_views[index] = buffer.getvalue()
for index, data in new_views.items():   # appended views; the old image bytes stay unreferenced in the buffer
    while len(binary) % 4:
        binary += b'\0'
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary += data
    doc['images'][index] = {'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                            'name': doc['images'][index].get('name', 'rock') + '_basalt'}
for material in doc['materials']:
    material['name'] = material['name'] + '_Basalt'
while len(binary) % 4:
    binary += b'\0'
doc['buffers'][0]['byteLength'] = len(binary)
encoded = json.dumps(doc, separators=(',', ':')).encode()
encoded += b' ' * (-len(encoded) % 4)
dst.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(encoded) + len(binary))
                + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
                + struct.pack('<II', len(binary), 0x004e4942) + bytes(binary))
print('WROTE', dst, len(new_views), 'colour images')
