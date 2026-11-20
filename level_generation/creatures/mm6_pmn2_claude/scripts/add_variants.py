#!/usr/bin/env python3
"""Colour variants pmn2_a/b/c (native palettes 801 red / 802 green / 803 blue) as KHR_materials_variants: the body
material is copied per tier and only gets extras.openyamm_tint (textures/tints.json); every copy shares the same
images, so the engine uploads the textures once. The staff is packed into the body material (one primitive).
Usage: add_variants.py in.glb out.glb"""
import copy, json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_glb(path):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
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
    tints = json.load(open(ROOT / 'textures' / 'tints.json'))['tints']
    body = next(i for i, m in enumerate(doc['materials']) if m['name'].startswith('Mage'))
    names = ['pmn2_a', 'pmn2_b', 'pmn2_c']
    index = {}
    for tier in 'abc':
        if tier == 'a':
            material = doc['materials'][body]; index['a'] = body
        else:
            material = copy.deepcopy(doc['materials'][body]); doc['materials'].append(material)
            index[tier] = len(doc['materials']) - 1
        material['name'] = f'Mage_{tier.upper()}'
        material.setdefault('extras', {})['openyamm_tint'] = tints[tier]
    mapped = 0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            m = primitive.get('material')
            if m == body:
                targets = [index[t] for t in 'abc']
            else:
                raise ValueError(f'unexpected primitive material {m}')
            primitive.setdefault('extensions', {})['KHR_materials_variants'] = {
                'mappings': [{'material': t, 'variants': [i]} for i, t in enumerate(targets)]}
            mapped += 1
    doc.setdefault('extensionsUsed', [])
    if 'KHR_materials_variants' not in doc['extensionsUsed']:
        doc['extensionsUsed'].append('KHR_materials_variants')
    doc.setdefault('extensions', {})['KHR_materials_variants'] = {'variants': [{'name': n} for n in names]}
    write_glb(dst, doc, binary)
    print('VARIANTS', names, 'primitives', mapped, 'tints', tints)


if __name__ == '__main__':
    main()
