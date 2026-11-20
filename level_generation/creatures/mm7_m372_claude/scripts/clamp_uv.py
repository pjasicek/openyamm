#!/usr/bin/env python3
"""Clamp every TEXCOORD_0 into [0, 1] in place (m372: LOD decimation pushed one LOD2 vertex to u = 1.0002, which
tools/merge_head_material.py refuses to pack). Args: <glb>"""
import json, struct, sys
import numpy as np
path = sys.argv[1]
raw = bytearray(open(path, 'rb').read()); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); base = 28 + n; fixed = 0; seen = set()
for m in doc['meshes']:
    for p in m['primitives']:
        ai = p['attributes'].get('TEXCOORD_0')
        if ai is None or ai in seen:
            continue
        seen.add(ai); a = doc['accessors'][ai]; bv = doc['bufferViews'][a['bufferView']]
        off = base + bv.get('byteOffset', 0) + a.get('byteOffset', 0); st = bv.get('byteStride', 8)
        for i in range(a['count']):
            for c in range(2):
                o = off + i * st + 4 * c; v = struct.unpack_from('<f', raw, o)[0]
                if v < 0.0 or v > 1.0:
                    struct.pack_into('<f', raw, o, min(1.0, max(0.0, v))); fixed += 1
        if 'min' in a:
            a['min'] = [max(0.0, x) for x in a['min']]; a['max'] = [min(1.0, x) for x in a['max']]
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
binary = raw[base:]
out = struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary)) + struct.pack('<II', len(enc), 0x4e4f534a) + enc + raw[20 + n:base] + binary
open(path, 'wb').write(out)
print('CLAMPUV', path, 'components clamped', fixed)
