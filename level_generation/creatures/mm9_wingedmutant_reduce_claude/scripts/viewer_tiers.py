#!/usr/bin/env python3
"""Review-viewer GLBs per tier for a Winged Mutant GLB (installed or reduced): three.js has no region ramps, so the
creature's approved viewer GLBs (../mm9_wingedmutant_claude/review/viewer/wmut_<t>.glb, r5 wing tone) supply each tier's
baked base colours (images '<prefix>_wmut_<t>'); this copies them into the given GLB with the tier's materials selected.
Same images for installed and reduced, so only geometry differs. Usage: viewer_tiers.py <glb> <suffix>
-> review/viewer/wmut_<t>_<suffix>.glb"""
import json, struct, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
CV = HERE.parent / 'mm9_wingedmutant_claude' / 'review' / 'viewer'
OUT = HERE / 'review' / 'viewer'; OUT.mkdir(parents=True, exist_ok=True)


def read_glb(path):
    raw = Path(path).read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write_glb(path, doc, binary):
    binary += b'\0' * (-len(binary) % 4); doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary)) + struct.pack('<II', len(enc), 0x4e4f534a)
                           + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)


glb, suffix = sys.argv[1], sys.argv[2]
for t in 'abc':
    vd, vb = read_glb(CV / f'wmut_{t}.glb')
    baked = {}
    for im in vd['images']:
        if im.get('name', '').endswith(f'_wmut_{t}'):
            bv = vd['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0)
            baked[im['name'][:-len(f'_wmut_{t}')]] = bytes(vb[o:o + bv['byteLength']])
    doc, binary = read_glb(glb)
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    S = t.upper()
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            prefix = doc['materials'][prim['material']]['name'].rsplit('_', 1)[0]
            prim['material'] = names[f'{prefix}_{S}']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'):
                prim.pop('extensions', None)
    for prefix, data in baked.items():
        mat = doc['materials'][names[f'{prefix}_{S}']]
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary += data
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'{prefix}_wmut_{t}'})
        doc['textures'].append({'source': len(doc['images']) - 1,
                                'sampler': doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)})
        mat['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
    if not doc['extensionsUsed']:
        doc.pop('extensionsUsed')
    write_glb(OUT / f'wmut_{t}_{suffix}.glb', doc, binary); print('viewer', f'wmut_{t}_{suffix}.glb', sorted(baked))
