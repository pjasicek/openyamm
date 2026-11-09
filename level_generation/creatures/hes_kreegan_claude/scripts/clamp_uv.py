#!/usr/bin/env python3
"""Clamp float TEXCOORD_* values into [0, 1] in a GLB, in place (accessor min/max updated). The shared LOD builder's
simplified LOD2/LOD3 can land a vertex at u = -0.00001 where the source UVs touch the atlas edge exactly (seen after
halve_lod0.py), and tools/merge_head_material.py rejects any value outside [0, 1]. Prints how many values moved and
the largest move; a large one would mean a real UV fault, not rounding. Args: <glb>"""
import json, struct, sys
import numpy as np
path = sys.argv[1]
raw = bytearray(open(path, 'rb').read())
n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n]); bin0 = 20 + n + 8
moved = 0; worst = 0.0; seen = set()
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        for key, ai in prim['attributes'].items():
            if not key.startswith('TEXCOORD') or ai in seen:
                continue
            seen.add(ai); acc = doc['accessors'][ai]
            if acc['componentType'] != 5126:
                continue
            bv = doc['bufferViews'][acc['bufferView']]
            if bv.get('byteStride', 8) not in (0, 8):
                raise SystemExit('interleaved texture coordinates are not supported')
            start = bin0 + bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
            a = np.frombuffer(raw, np.float32, acc['count'] * 2, start).reshape(-1, 2).copy()
            c = np.clip(a, 0.0, 1.0); d = np.abs(c - a)
            if d.max() > 0:
                moved += int((d > 0).sum()); worst = max(worst, float(d.max()))
                raw[start:start + c.nbytes] = c.astype(np.float32).tobytes()
                acc['min'] = [float(x) for x in c.min(0)]; acc['max'] = [float(x) for x in c.max(0)]
js = json.dumps(doc, separators=(',', ':')).encode()
js += b' ' * ((4 - len(js) % 4) % 4)
out = bytearray(raw[:12]) + struct.pack('<I', len(js)) + b'JSON' + js + raw[20 + n:]
struct.pack_into('<I', out, 8, len(out))
open(path, 'wb').write(out)
print('CLAMPUV', path, 'values moved', moved, 'largest move', f'{worst:.2e}')
if worst > 1e-3:
    raise SystemExit('a texture coordinate moved more than 1e-3: check the UVs')
