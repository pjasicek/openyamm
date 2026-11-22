#!/usr/bin/env python3
"""Write a copy of a linked creature GLB whose LOD meshes (extras openyamm_lods) are scene nodes again, skinned like
the base node, named Titan_LOD<n>, so Blender's importer brings them in. Usage: expose_lods.py in.glb out.glb"""
import json
import struct
import sys

raw = open(sys.argv[1], 'rb').read()
size = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + size])
rest = raw[20 + size:]
base_i = next(i for i, n in enumerate(doc['nodes']) if n.get('mesh') == 0)
base = doc['nodes'][base_i]
parent = next(i for i, n in enumerate(doc['nodes']) if base_i in n.get('children', []))
for k, mesh in enumerate(doc['meshes'][0]['extras']['openyamm_lods'], 1):
    node = {'mesh': mesh, 'name': f'Titan_LOD{k}', 'skin': base['skin']}
    for key in ('translation', 'rotation', 'scale'):
        if key in base:
            node[key] = base[key]
    doc['nodes'].append(node)
    doc['nodes'][parent]['children'].append(len(doc['nodes']) - 1)
enc = json.dumps(doc, separators=(',', ':')).encode()
enc += b' ' * (-len(enc) % 4)
out = struct.pack('<III', 0x46546c67, 2, 12 + 8 + len(enc) + len(rest)) + struct.pack('<II', len(enc), 0x4e4f534a) + enc + rest
open(sys.argv[2], 'wb').write(out)
