"""Where the head's fixed triangle order shows the wrong face: orthographic rays from az/el, front faces only; nearest hit against the last-drawn hit. Args: glb az el [png]"""
import sys, math
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1]); m = Model(g)
doc = g.json
mesh = next(x for x in doc['meshes'] if x.get('name') == 'Ghost')
names = [doc['materials'][p['material']]['name'] for p in mesh['primitives']]
i = [k for k, n in enumerate(names) if n.startswith('GhostHead')][0]
pr = m.primitives[i]
P, T = pr['positions'], pr['triangles']
az, el = math.radians(float(sys.argv[2])), math.radians(float(sys.argv[3]))
v = np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)])
r = np.array([math.cos(az), 0, -math.sin(az)]); u = np.cross(v, r)
A, B, C = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
n = np.cross(B - A, C - A); front = (n @ v) > 0
c = 0.5 * (P.min(0) + P.max(0))
RES = 220
span = np.linspace(-0.14, 0.14, RES)
out = np.zeros((RES, RES), np.uint8); bad = 0; tot = 0
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
            uu = f * (s * h).sum(1); q = np.cross(s, E1[idxf]); vv = f * (q * d).sum(1); t = f * (E2[idxf] * q).sum(1)
        hit = (np.abs(det) > 1e-12) & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (t > 0)
        if not hit.any():
            continue
        ids = idxf[hit]; ts = t[hit]
        near = ids[ts.argmin()]; last = ids.max()
        tot += 1
        out[iy, ix] = 120
        if near != last:
            bad += 1; out[iy, ix] = 255
            inv.append((ix, iy, near, last, float(ts.max() - ts.min())))
print('rays', tot, 'wrong', bad)
if inv:
    I = np.array(inv)
    # the top faces shown wrongly
    u_, cnt = np.unique(I[:, 3].astype(int), return_counts=True)
    for f, k in sorted(zip(u_, cnt), key=lambda x: -x[1])[:10]:
        ce = P[T[f]].mean(0)
        print('last-drawn face', f, 'pixels', k, 'centre', ce.round(3), 'dist', round(float(np.linalg.norm(ce - c)), 3), 'normal.dot(out)', round(float(n[f] @ (ce - c) / np.linalg.norm(n[f]) / np.linalg.norm(ce - c)), 2))
if len(sys.argv) > 4:
    from PIL import Image
    Image.fromarray(out).save(sys.argv[4])
