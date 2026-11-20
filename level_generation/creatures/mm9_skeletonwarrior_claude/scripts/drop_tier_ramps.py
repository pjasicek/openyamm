#!/usr/bin/env python3
"""The Master tier IS the paint: its materials lose the region mask and ramps, so its colours are not flattened by a luminance
ramp (fit error 15 levels on the lacquer) and every tier still shares every image. Args: <in> <out> <variant>"""
import json, struct, sys
IN, OUT, VAR = sys.argv[1:4]
data = open(IN, 'rb').read()
jl = struct.unpack_from('<I', data, 12)[0]
doc = json.loads(data[20:20 + jl]); rest = data[20 + jl:]
n = 0
for m in doc['materials']:
    if VAR in m.get('name', ''):
        ex = m.get('extras', {})
        for k in ('openyamm_region_mask', 'openyamm_region_ramps'):
            if ex.pop(k, None) is not None: n += 1
print('dropped', n, [m.get('name') for m in doc['materials']])
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
total = 20 + len(j) + len(rest)
open(OUT, 'wb').write(struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(j), 0x4E4F534A) + j + rest)
