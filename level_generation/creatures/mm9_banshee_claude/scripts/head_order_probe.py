#!/usr/bin/env python3
"""Where the head's fixed triangle order shows the wrong face, posed: orthographic rays from az/el, front faces only; nearest hit against the last-drawn hit. Also what paint the visible texel has: dark texels under the nearest hit mean paint, a nearest face with a light texel under a dark last-drawn one means order.
Args: glb clip time az el [out png] [out sheet of worst faces]. Run from the project folder."""
import sys, math
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1]); m = Model(g)
clip, t_, azd, eld = sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
doc = g.json
mesh = next(x for x in doc['meshes'] if x.get('name') == 'Banshee')
names = [doc['materials'][p['material']]['name'] for p in mesh['primitives']]
i = [k for k, n in enumerate(names) if n.startswith('BansheeHead')][0]
pr = m.primitives[i]
sk = m.skinned_positions(m.world(m.sample(clip, t_)))[i]
P, T = sk[0], np.asarray(sk[1]).reshape(-1, 3)
az, el = math.radians(azd), math.radians(eld)
v = np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])
r = np.array([math.cos(az), 0, -math.sin(az)]); u = np.cross(v, r)
A, B, C = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
n = np.cross(B - A, C - A); front = (n @ v) > 0
c = P.mean(0)
RES = 260
span = np.linspace(-0.2, 0.2, RES)
out = np.zeros((RES, RES, 3), np.uint8); bad = 0; tot = 0
E1, E2 = B - A, C - A
idxf = np.where(front)[0]
inv = []
for iy, b in enumerate(span[::-1]):
    for ix, a in enumerate(span):
        o = c + r * a + u * b + v * 2
        d = -v
        h = np.cross(d, E2[idxf]); det = (E1[idxf] * h).sum(1)
        s = o - A[idxf]
        with np.errstate(divide='ignore', invalid='ignore'):
            f = 1 / det
            uu = f * (s * h).sum(1); q = np.cross(s, E1[idxf]); vv = f * (q * d).sum(1); tt = f * (E2[idxf] * q).sum(1)
        hit = (np.abs(det) > 1e-12) & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (tt > 0)
        if not hit.any():
            continue
        ids = idxf[hit]; ts = tt[hit]
        near = ids[ts.argmin()]; last = ids.max()
        tot += 1
        out[iy, ix] = (90, 90, 90)
        if near != last and ts.max() - ts.min() > 0.002:
            bad += 1; out[iy, ix] = (255, 40, 40)
            inv.append((ix, iy, near, last, float(ts[ids == last][0] - ts.min())))
print(clip, t_, 'az', azd, 'el', eld, 'rays', tot, 'wrong', bad, 'share %.2f %%' % (100 * bad / max(tot, 1)))
if inv:
    I = np.array(inv)
    u_, cnt = np.unique(I[:, 3].astype(int), return_counts=True)
    for f, k in sorted(zip(u_, cnt), key=lambda x: -x[1])[:8]:
        ce = pr['positions'][T[f]].mean(0)
        print(' last-drawn face', f, 'of', len(T), 'pixels', k, 'rest centre', ce.round(3), 'depth behind nearest %.3f' % I[I[:, 3] == f, 4].mean())
if len(sys.argv) > 6:
    Image.fromarray(out).resize((RES * 3, RES * 3), Image.NEAREST).save(sys.argv[6])
