#!/usr/bin/env python3
"""Where the mallet goes into the body in one clip (mallet_gate.py's depth test, per vertex): worst vertices, frames and
their position in the mallet's own frame (t along the shaft axis of work/mallet_geom.json). Usage: <glb> <clip>"""
import sys, json
import numpy as np
sys.argv = [sys.argv[0], sys.argv[1], '/dev/null', sys.argv[2]]
clip = sys.argv[3]
src = open('scripts/mallet_gate.py').read().split('out = {}')[0]
exec(compile(src, 'mallet_gate_head', 'exec'))
G = json.load(open('work/mallet_geom.json')); c0, ax0 = np.array(G['shaft_c']), np.array(G['shaft_ax'])
restP = np.concatenate([m.primitives[k]['positions'] for k in USE])
T_ = m.clip_times(clip); best = []
for t in np.arange(0, T_[-1] + 1e-6, 1 / 24):
    w = m.world(m.sample(clip, float(t))); X = skin(w); dd = depth(X[mv], X)
    k = int(dd.argmax()); best.append((float(dd[k]), round(float(t), 3), int(mv[k])))
best.sort(reverse=True)
for dm, t, v in best[:5]:
    p = restP[v]; tt = float((p - c0) @ ax0); r = float(np.linalg.norm((p - c0) - tt * ax0))
    print(f'depth {dm*100:.2f} cm at {t:.3f} s, vertex {v}: t {tt:.3f} r {r:.3f}')
# dense: points spread over the mallet's triangles (rigid on Xhammer, so interpolating skinned corners is exact)
mt = tris[mal[tris].all(1)]
A = restP[mt[:, 0]]; B = restP[mt[:, 1]]; C = restP[mt[:, 2]]; area = 0.5 * np.linalg.norm(np.cross(B - A, C - A), axis=1)
rng = np.random.default_rng(1); n = 20000; fi = rng.choice(len(mt), n, p=area / area.sum()); u = rng.random(n); v = rng.random(n)
fl = u + v > 1; u[fl] = 1 - u[fl]; v[fl] = 1 - v[fl]
res = []
for t in np.arange(0, T_[-1] + 1e-6, 1 / 24):
    w = m.world(m.sample(clip, float(t))); X = skin(w)
    pts = X[mt[fi, 0]] + (X[mt[fi, 1]] - X[mt[fi, 0]]) * u[:, None] + (X[mt[fi, 2]] - X[mt[fi, 0]]) * v[:, None]
    dd = depth(pts, X); res.append((float(dd.max()), round(float(t), 3), int((dd > 0.01).sum())))
res.sort(reverse=True)
print('DENSE surface', [(round(a * 100, 2), b, c) for a, b, c in res[:4]], 'frames > 1 cm', sum(1 for r_ in res if r_[0] > 0.01))
