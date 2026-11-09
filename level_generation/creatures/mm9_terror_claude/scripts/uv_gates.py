#!/usr/bin/env python3
"""UV gates of a dump_uv3d.py npz at 2K: texels covered by two faces of different islands' surfaces (the Terror's belly
shards came from these), zero-area triangles. Usage: uv_gates.py <uv3d.npz> [out.json]"""
import json, sys
import numpy as np

d = np.load(sys.argv[1])
S = 2048
uv = d['uv'] * S
owner = -np.ones((S, S), np.int32)
double = np.zeros((S, S), bool)
pairs = set()
zero = 0
for t, p in enumerate(uv):
    a, b, c = p
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-6:
        zero += 1
        continue
    x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), S - 1)
    y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
    l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
    ins = (l1 > 1e-3) & (l2 > 1e-3) & (1 - l1 - l2 > 1e-3)
    iy, ix = np.nonzero(ins)
    iy, ix = iy + y0, ix + x0
    prev = owner[iy, ix]
    dup = prev >= 0
    double[iy[dup], ix[dup]] = True
    pairs.update((int(q), t) for q in np.unique(prev[dup]))
    owner[iy, ix] = t
r = {'triangles': len(uv), 'zero_area_triangles': zero, 'texels_painted_twice': int(double.sum()), 'face_pairs': len(pairs),
     'texels_used': int((owner >= 0).sum()), 'atlas_use': round(float((owner >= 0).mean()), 4)}
print('UV_GATES', json.dumps(r))
if len(sys.argv) > 2:
    json.dump(r, open(sys.argv[2], 'w'), indent=1)
