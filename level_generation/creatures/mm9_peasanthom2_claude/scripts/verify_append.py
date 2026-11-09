#!/usr/bin/env python3
"""Proof that add_tier.py only appended: every bufferView of the old GLB has byte-identical data at the same offset in the
new one; every old accessor, image, texture, sampler, material, node, skin, animation and mesh JSON entry is identical
except the primitives' variant mapping lists, whose old entries are identical and come first; old variant names identical.
Usage: verify_append.py <old glb> <new glb>"""
import sys, json, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
a, ab = RV.read_glb(sys.argv[1]); b, bb = RV.read_glb(sys.argv[2])
bad = []
for i, bv in enumerate(a['bufferViews']):
    o, n = bv.get('byteOffset', 0), bv['byteLength']
    if b['bufferViews'][i] != bv or ab[o:o + n] != bb[o:o + n]:
        bad.append(('bufferView', i))
for key in ('accessors', 'images', 'textures', 'samplers', 'materials', 'nodes', 'skins', 'animations', 'scenes'):
    for i, x in enumerate(a.get(key, [])):
        if b[key][i] != x:
            bad.append((key, i))
for i, m in enumerate(a['meshes']):
    mb = b['meshes'][i]
    for j, p in enumerate(m['primitives']):
        p2 = copy.deepcopy(mb['primitives'][j]); q = copy.deepcopy(p)
        ma = q.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
        mbm = p2.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
        if mbm[:len(ma)] != ma:
            bad.append(('mapping', m['name'], j))
        for d in (p2, q):
            d.get('extensions', {}).pop('KHR_materials_variants', None)
        if p2 != q:
            bad.append(('primitive', m['name'], j))
va = a['extensions']['KHR_materials_variants']['variants']; vb = b['extensions']['KHR_materials_variants']['variants']
if vb[:len(va)] != va:
    bad.append(('variants',))
print('VERIFY_APPEND', 'OK' if not bad else 'FAIL', json.dumps(dict(old_bufferViews=len(a['bufferViews']), new_bufferViews=len(b['bufferViews']),
      old_buffer=len(ab), new_buffer=len(bb), variants=[v['name'] for v in vb], new_materials=[m['name'] for m in b['materials'][len(a['materials']):]],
      new_images=[im['name'] for im in b['images'][len(a['images']):]], problems=bad[:20])))
