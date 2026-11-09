#!/usr/bin/env python3
"""Add KHR_materials_variants to a boss GLB: variant 0 keeps every material; each further variant maps the listed
materials to copies (name + '_' + variant). Run before claude_shared/emission.py, which then colours each variant's
copy (`--color VARIANT=r,g,b`). Usage: add_variants.py in.glb out.glb <base_variant> <variant> MATERIAL [MATERIAL...]"""
import json, struct, sys
from pathlib import Path


def read(path):
    raw = Path(path).read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4); doc['buffers'][0]['byteLength'] = len(binary)
    js = json.dumps(doc, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binary))
                           + struct.pack('<II', len(js), 0x4E4F534A) + js
                           + struct.pack('<II', len(binary), 0x004E4942) + binary)


src, dst, base, other, *mats = sys.argv[1:]
doc, binary = read(src)
names = [m['name'] for m in doc['materials']]
copies = {}
for name in mats:
    i = names.index(name)
    m = json.loads(json.dumps(doc['materials'][i])); m['name'] = f'{name}_{other}'
    doc['materials'].append(m); copies[i] = len(doc['materials']) - 1
doc.setdefault('extensions', {})['KHR_materials_variants'] = {'variants': [{'name': base}, {'name': other}]}
doc.setdefault('extensionsUsed', [])
if 'KHR_materials_variants' not in doc['extensionsUsed']:
    doc['extensionsUsed'].append('KHR_materials_variants')
n = 0
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        m = p.get('material')
        maps = [{'material': m, 'variants': [0] + ([] if m in copies else [1])}]
        if m in copies:
            maps.append({'material': copies[m], 'variants': [1]}); n += 1
        p.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': maps}
write(dst, doc, binary)
print('VARIANTS', base, other, 'copied', [doc['materials'][c]['name'] for c in copies.values()], 'primitives', n)
