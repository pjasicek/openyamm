#!/usr/bin/env python3
"""Top/side point plots and foot clusters of a raw Meshy GLB (Blender axes: x left, y back, z up). Args: glb out.png"""
import json, struct, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.cluster.vq import kmeans2
raw = open(sys.argv[1], 'rb').read()
n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n]); b = raw[28 + n:]
pts = []
for m in doc['meshes']:
    for pr in m['primitives']:
        acc = doc['accessors'][pr['attributes']['POSITION']]; bv = doc['bufferViews'][acc['bufferView']]
        pts.append(np.frombuffer(b, np.float32, acc['count'] * 3, bv.get('byteOffset', 0) + acc.get('byteOffset', 0)).reshape(-1, 3))
p = np.concatenate(pts)
P = np.stack([p[:, 0], -p[:, 2], p[:, 1]], 1); P[:, 2] -= P[:, 2].min()
print('BBOX', P.min(0).round(3), P.max(0).round(3), 'verts', len(P))
im = Image.new('RGB', (1600, 800), (255, 255, 255)); d = ImageDraw.Draw(im)
for q in P[np.argsort(P[:, 2])]:
    c = int(255 * min(q[2] / 0.5, 1)); d.point((400 + q[0] * 700, 400 + q[1] * 700), fill=(c, 0, 255 - c))
for q in P[np.argsort(P[:, 0])]:
    c = int(255 * min((q[0] + 0.35) / 0.7, 1)); d.point((1200 + q[1] * 700, 600 - q[2] * 700), fill=(c, 0, 255 - c))
im.save(sys.argv[2])
low = P[P[:, 2] < 0.04]
c, l = kmeans2(low[:, :2], 6, seed=1, minit='++')
for k in np.argsort(c[:, 1]):
    print('FOOT', c[k].round(3), int((l == k).sum()))
