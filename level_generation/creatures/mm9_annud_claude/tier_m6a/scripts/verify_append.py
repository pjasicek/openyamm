#!/usr/bin/env python3
"""Proof that add_tier.py only appended to the approved Annud GLB: every old bufferView entry and its bytes are identical
at the same offset; every old accessor, image, texture, sampler, material, node, skin, animation, scene and mesh JSON
entry is identical, except that primitives may gain a KHR_materials_variants extension (nothing else on them changes);
the only new root keys are the KHR_materials_variants extension and its extensionsUsed entry.
Usage: verify_append.py <old glb> <new glb>"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared'))
import region_variants as RV  # noqa: E402

a, ab = RV.read_glb(sys.argv[1])
b, bb = RV.read_glb(sys.argv[2])
bad = []
for i, bv in enumerate(a['bufferViews']):
    o, n = bv.get('byteOffset', 0), bv['byteLength']
    if b['bufferViews'][i] != bv or ab[o:o + n] != bb[o:o + n]:
        bad.append(('bufferView', i))
if bb[:len(ab)] != ab:
    bad.append(('buffer prefix',))
for key in ('accessors', 'images', 'textures', 'samplers', 'materials', 'nodes', 'skins', 'animations', 'scenes'):
    if len(b.get(key, [])) < len(a.get(key, [])):
        bad.append((key, 'shorter'))
    for i, x in enumerate(a.get(key, [])):
        if b[key][i] != x:
            bad.append((key, i))
if len(a['meshes']) != len(b['meshes']):
    bad.append(('meshes', 'count'))
mapped = 0
for i, m in enumerate(a['meshes']):
    mb = copy.deepcopy(b['meshes'][i])
    for p in mb['primitives']:
        ext = p.get('extensions', {})
        if ext.pop('KHR_materials_variants', None) is not None:
            mapped += 1
        if not ext:
            p.pop('extensions', None)
    if mb != m:
        bad.append(('mesh', m.get('name'), i))
root_a = {k: v for k, v in a.items() if k not in ('buffers', 'bufferViews', 'accessors', 'images', 'textures',
                                                 'samplers', 'materials', 'meshes')}
root_b = {k: v for k, v in b.items() if k not in ('buffers', 'bufferViews', 'accessors', 'images', 'textures',
                                                 'samplers', 'materials', 'meshes')}
ext_b = dict(root_b.pop('extensions', {}))
ext_b.pop('KHR_materials_variants', None)
if ext_b:
    root_b['extensions'] = ext_b
used = [u for u in root_b.pop('extensionsUsed', []) if u != 'KHR_materials_variants']
if used:
    root_b['extensionsUsed'] = used
for k in ('nodes', 'skins', 'animations', 'scenes'):
    root_a.pop(k, None); root_b.pop(k, None)
if root_a != root_b:
    bad.append(('root', sorted(set(root_a) ^ set(root_b))))
print('VERIFY_APPEND', 'OK' if not bad else 'FAIL', json.dumps(dict(
    old_bufferViews=len(a['bufferViews']), new_bufferViews=len(b['bufferViews']), old_buffer=len(ab),
    new_buffer=len(bb), variants=[v['name'] for v in b['extensions']['KHR_materials_variants']['variants']],
    mapped_primitives=mapped, new_materials=[m['name'] for m in b['materials'][len(a['materials']):]],
    new_images=[im['name'] for im in b['images'][len(a['images']):]], problems=bad[:20])))
