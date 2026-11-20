#!/usr/bin/env python3
"""Meshy v3 return -> Blender axes, forward -Y (rotated +90 deg about Z), body widened by WIDEN in x, scaled so the
back stands HEIGHT m, grounded. Writes work/body_norm.npy (vertex positions) for analysis."""
import json, struct, sys
import numpy as np
WIDEN, HEIGHT = 1.12, 1.2
raw = open(sys.argv[1], 'rb').read()
n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n]); b = raw[28 + n:]
acc = doc['accessors'][doc['meshes'][0]['primitives'][0]['attributes']['POSITION']]; bv = doc['bufferViews'][acc['bufferView']]
p = np.frombuffer(b, np.float32, acc['count'] * 3, bv.get('byteOffset', 0) + acc.get('byteOffset', 0)).reshape(-1, 3)
P = np.stack([p[:, 0], -p[:, 2], p[:, 1]], 1).astype(np.float64)
P = np.stack([-P[:, 1], P[:, 0], P[:, 2]], 1)          # +90 deg about Z: head (-x) -> -y
P[:, 0] *= WIDEN
P[:, 2] -= P[:, 2].min()
P *= HEIGHT / P[:, 2].max()
P[:, 0] -= (P[:, 0].max() + P[:, 0].min()) / 2
print('BBOX', P.min(0).round(3), P.max(0).round(3))
np.save(sys.argv[2], P)
