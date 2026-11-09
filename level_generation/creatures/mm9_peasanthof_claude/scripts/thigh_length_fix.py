#!/usr/bin/env python3
"""Thigh joint offsets kept at their rest length (finishing round 2026-11-04, HOF2 bone_length_audit: Bip01 L Thigh 0.171-0.202 m
across AttackMelee/Hit/Death against 0.192 at rest, an 18 % stretch). clips_mm9.py adds MM9's per-frame thigh offsets (the
source keeps their LENGTH but turns them) to our refitted rest, which changes the length. Every translation key of the named
joints is rescaled to the joint's rest length, direction kept (the hip sway stays). In place on a copy; keys only.
Args: <in glb> <out glb> [joint names, default 'Bip01 L Thigh,Bip01 R Thigh']"""
import json, struct, sys
import numpy as np
src, dst = sys.argv[1], sys.argv[2]
names = (sys.argv[3] if len(sys.argv) > 3 else 'Bip01 L Thigh,Bip01 R Thigh').split(',')
d = bytearray(open(src, 'rb').read())
jl = struct.unpack('<I', d[12:16])[0]; j = json.loads(d[20:20 + jl]); b0 = 20 + jl + 8
nodes = j['nodes']; ids = {i: n for i, n in enumerate(nodes) if n.get('name') in names}
done = 0; worst = 0.0
for an in j.get('animations', []):
    for c in an['channels']:
        n = c['target'].get('node')
        if n not in ids or c['target'].get('path') != 'translation':
            continue
        a = j['accessors'][an['samplers'][c['sampler']]['output']]; v = j['bufferViews'][a['bufferView']]
        assert a['componentType'] == 5126 and a['type'] == 'VEC3' and not v.get('byteStride')
        off = b0 + v.get('byteOffset', 0) + a.get('byteOffset', 0)
        arr = np.frombuffer(bytes(d[off:off + 12 * a['count']]), '<f4').reshape(-1, 3).astype(float)
        rl = np.linalg.norm(ids[n].get('translation', [0, 0, 0])); L = np.linalg.norm(arr, axis=1)
        worst = max(worst, float(np.abs(L / rl - 1).max()))
        arr = arr * (rl / np.maximum(L, 1e-9))[:, None]
        d[off:off + 12 * a['count']] = arr.astype('<f4').tobytes(); done += 1
        if 'min' in a: a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
out = bytearray(d[:12]) + struct.pack('<I', len(js)) + b'JSON' + js + d[20 + jl:]
struct.pack_into('<I', out, 8, len(out))
open(dst, 'wb').write(out)
print('THIGHLEN', dst, 'channels', done, 'worst stretch before', round(worst * 100, 1), '%')
