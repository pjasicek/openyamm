#!/usr/bin/env python3
"""Halberd held the wrong way round (follow-up 5, user 2026-11-12: "attacks with the wrong end"). place_halberd.py took the
axe crescent as the larger side of the head (-X of the old attachment); the back spike reaches further (0.32 m from the
shaft axis against the crescent's 0.22 m), so the crescent was seated where MM9's spike side is: in Attack (0.23-0.40 s)
and Attack2 (0.13-0.50 s) the spike led into the blow (spike side . head velocity +0.9) and the crescent faced backward.
Fix: the attachment is turned 180 deg about its own shaft axis (a line fitted to the shaft, in Xbase space), every mesh and
LOD, positions and normals: the shaft stays in the fist, only the head turns. The model itself is unchanged.
Args: <in halberd glb> <out glb>"""
import sys
import numpy as np
from glbtool import Glb, Model
IN, OUT = sys.argv[1:3]
g = Glb(IN); m = Model(g); d = g.json
V = np.concatenate([p['positions'] for p in m.primitives])
c = V.mean(0); ax = np.linalg.svd(V - c)[2][0]
t = (V - c) @ ax
if np.ptp(V[t > t.max() - 0.3] - c, 0).max() < np.ptp(V[t < t.min() + 0.3] - c, 0).max(): ax = -ax; t = -t   # +ax toward the head
shaft = V[(t > t.min() + 0.1) & (t < t.max() - 0.45)]                 # bare shaft: no head, no butt cap
p0 = shaft.mean(0); ax = np.linalg.svd(shaft - p0)[2][0] * np.sign(np.linalg.svd(shaft - p0)[2][0] @ ax)
R = 2 * np.outer(ax, ax) - np.eye(3)                                    # 180 deg about ax
r = np.linalg.norm((shaft - p0) - np.outer((shaft - p0) @ ax, ax), axis=1)
print('HALBERD shaft axis', ax.round(4), 'through', p0.round(4), 'shaft radius %.4f..%.4f' % (r.min(), r.max()))
done = set()
for mesh in d['meshes']:
    for pr in mesh['primitives']:
        for key, kind in ((pr['attributes'].get('POSITION'), 'p'), (pr['attributes'].get('NORMAL'), 'n')):
            if key is None or key in done: continue
            done.add(key); a = d['accessors'][key]; v = d['bufferViews'][a['bufferView']]
            off = v.get('byteOffset', 0) + a.get('byteOffset', 0); assert v.get('byteStride', 12) == 12
            X = np.frombuffer(bytes(g.bin[off:off + a['count'] * 12]), np.float32).reshape(-1, 3).astype(float)
            Y = (X - p0) @ R.T + p0 if kind == 'p' else X @ R.T
            if kind == 'p': a['min'] = Y.min(0).tolist(); a['max'] = Y.max(0).tolist()
            g.bin[off:off + a['count'] * 12] = Y.astype(np.float32).tobytes()
g.write(OUT)
print('HALBERD rolled 180 deg', OUT, 'accessors', len(done))
