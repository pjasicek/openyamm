#!/usr/bin/env python3
"""Extents of exported GLBs in game units (1 model metre = 100): LOD0 node's POSITION accessor bounds (glTF Y up,
+Z front), the plan radius from the origin, and the LOD triangle counts. Usage: measure.py <glb> [...]"""
import json
import struct
import sys

import numpy as np

for path in sys.argv[1:]:
    data = open(path, 'rb').read()
    n = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + n])
    binoff = 20 + n + 8
    tris = {}
    pos_all = None
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        mesh = doc['meshes'][node['mesh']]
        t = 0
        for prim in mesh['primitives']:
            t += doc['accessors'][prim['indices']]['count'] // 3
        tris[node['name']] = t
        if '_LOD' not in node['name']:
            prim = mesh['primitives'][0]
            acc = doc['accessors'][prim['attributes']['POSITION']]
            bv = doc['bufferViews'][acc['bufferView']]
            off = binoff + bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
            pos_all = np.frombuffer(data, np.float32, acc['count'] * 3, off).reshape(-1, 3)
    lo, hi = pos_all.min(0) * 100, pos_all.max(0) * 100
    r = np.hypot(pos_all[:, 0], pos_all[:, 2]).max() * 100
    print('%-34s height %.1f (y %.1f..%.1f)  x %.0f..%.0f  front(+z) %.0f..%.0f  plan r %.0f  tris %s' % (
        path.split('/')[-1], hi[1] - lo[1], lo[1], hi[1], lo[0], hi[0], lo[2], hi[2], r, list(tris.values())))
