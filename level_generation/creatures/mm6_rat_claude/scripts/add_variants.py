#!/usr/bin/env python3
"""Append skin B/C base-colour textures and KHR_materials_variants (rat_a/b/c) to every primitive of a GLB.
Usage: add_variants.py in.glb out.glb"""
import copy
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_glb(path):
    raw = path.read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    doc, binary = read_glb(src)
    if len(doc['materials']) != 1:
        raise ValueError('Expected the single skin-A material')
    base = doc['materials'][0]
    base['name'] = 'Rat_A'
    material_index = {'rat_a': 0}
    for skin in ('b', 'c'):
        png = (ROOT / 'textures' / f'rat_{skin}_basecolor_graded.png').read_bytes()
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(png)})
        binary += png
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'rat_{skin}_basecolor'})
        texture = copy.deepcopy(doc['textures'][base['pbrMetallicRoughness']['baseColorTexture']['index']])
        texture['source'] = len(doc['images']) - 1
        doc['textures'].append(texture)
        material = copy.deepcopy(base)
        material['name'] = f'Rat_{skin.upper()}'
        material['pbrMetallicRoughness']['baseColorTexture']['index'] = len(doc['textures']) - 1
        doc['materials'].append(material)
        material_index[f'rat_{skin}'] = len(doc['materials']) - 1
    names = ['rat_a', 'rat_b', 'rat_c']
    mapped = 0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            if primitive.get('material') != 0:
                raise ValueError('Unexpected primitive material')
            primitive.setdefault('extensions', {})['KHR_materials_variants'] = {
                'mappings': [{'material': material_index[n], 'variants': [i]} for i, n in enumerate(names)]}
            mapped += 1
    doc.setdefault('extensionsUsed', [])
    if 'KHR_materials_variants' not in doc['extensionsUsed']:
        doc['extensionsUsed'].append('KHR_materials_variants')
    doc.setdefault('extensions', {})['KHR_materials_variants'] = {'variants': [{'name': n} for n in names]}
    write_glb(dst, doc, binary)
    print(f'{dst}: {len(names)} variants mapped on {mapped} primitives')


if __name__ == '__main__':
    main()
