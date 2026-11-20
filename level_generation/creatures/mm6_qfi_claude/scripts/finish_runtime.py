#!/usr/bin/env python3
"""Material extras on the merged runtime GLB (export/mm6_qfi.glb, in place): the queen's merged body/head material and
the rock read specular per texel from the packed metal/roughness red channel (openyamm_specular_mask; compose_qfi.py
writes metal 0.8, horns 0.3, skin 0.12, rock 0.1), metallic and roughness come from the maps (factors 1)."""
import json
import struct
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]


def read_glb(path):
    data = path.read_bytes()
    offset, document, binary = 12, None, b''
    while offset < len(data):
        size, kind = struct.unpack_from('<II', data, offset)
        chunk = data[offset + 8:offset + 8 + size]
        if kind == 0x4E4F534A:
            document = json.loads(chunk)
        else:
            binary = chunk
        offset += 8 + size
    return document, binary


def write_glb(path, document, binary):
    text = json.dumps(document, separators=(',', ':')).encode()
    text += b' ' * (-len(text) % 4)
    binary = bytes(binary) + b'\0' * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    path.write_bytes(struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(text), 0x4E4F534A) + text
                     + struct.pack('<II', len(binary), 0x004E4942) + binary)


path = P / 'export' / 'mm6_qfi.glb'
doc, binary = read_glb(path)
names = []
for m in doc['materials']:
    m.setdefault('extras', {})['openyamm_specular_mask'] = True
    pbr = m.setdefault('pbrMetallicRoughness', {})
    pbr['metallicFactor'] = 1.0
    pbr['roughnessFactor'] = 1.0
    names.append(m.get('name'))
write_glb(path, doc, binary)
print('FINISH materials', names)
