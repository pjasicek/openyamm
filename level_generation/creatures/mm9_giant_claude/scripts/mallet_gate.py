#!/usr/bin/env python3
"""Grip and mallet gate, every clip at 24 fps on the runtime GLB:
- grip: right-hand finger and thumb vertices against the shaft (radius R from make_mallet.py): deepest point inside the shaft (cm),
  and the fist's wrap: the angle round the shaft covered by finger vertices within 1.5 cm of its surface (deg, median over frames);
- mallet in the body: mallet vertices behind the body's outer surface (not the right arm), deepest (cm) and frames over 1 cm;
- left hand: the deepest left finger vertex inside the shaft (cm) where it holds it.
Args: <glb> [out json]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor')); sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
from outer_surface import outer_faces
R = 0.030                     # third pass: the shaft fitted to the fists
m = Model(Glb(sys.argv[1])); d = m.glb.json; names = [n.get('name') for n in d['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tris, dom, off = [], [], 0
for k in USE:
    pr = P[k]; tris.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tris); dom = np.concatenate(dom)
FING = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
rf = np.where(np.array([' R ' in x and any(k in x for k in FING) for x in dom]))[0]
lf = np.where(np.array([' L ' in x and any(k in x for k in FING) for x in dom]))[0]
mal = np.isin(dom, ['Xhammer', 'Xbase']); mv = np.where(mal)[0]
rarm = np.array([' R ' in x for x in dom])
def skin(w):
    sp = m.skinned_positions(w); return np.concatenate([sp[k][0] for k in USE])
rest = skin(m.world({}))
body = np.where(~mal[tris].any(1) & ~rarm[tris].any(1))[0]; body = body[outer_faces(rest, tris, body)]
iX = names.index('Xhammer')
def depth(pts, X):
    T = X[tris[body]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    _, near = cKDTree((a + b + c) / 3).query(pts, k=24)
    rp = np.repeat(pts, near.shape[1], 0)
    q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
    dd = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = dd.argmin(1); rows = np.arange(len(pts))
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
    return np.where((side < 0) & (dd[rows, best] <= 0.08), -side, 0.0)
out = {}
for an in d['animations']:
    c = an['name']; T_ = m.clip_times(c); dur = T_[-1]
    gin, wraps, lin, mdep, mfr = 0, [], 0, 0, 0
    for t in np.arange(0, dur + 1e-6, 1 / 24):
        w = m.world(m.sample(c, float(t))); X = skin(w)
        o = w[iX][:3, 3]; a = w[iX][:3, 1] / np.linalg.norm(w[iX][:3, 1])
        def rad(ids):
            v = X[ids] - o; al = v @ a; r = np.linalg.norm(v - np.outer(al, a), axis=1); return r, al
        r, al = rad(rf); on = (al > -0.38) & (al < 1.27)
        gin = max(gin, float((R - r[on]).max()) if on.any() else 0)
        near = on & (r < R + 0.015)
        if near.sum() > 5:
            v = X[rf[near]] - o; v = v - np.outer(v @ a, a); e1 = np.cross(a, [0, 1, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(a, e1)
            ang = np.sort(np.degrees(np.arctan2(v @ e2, v @ e1)))
            gaps = np.diff(np.r_[ang, ang[0] + 360]); wraps.append(360 - gaps.max())
        r, al = rad(lf); on = (al > -0.38) & (al < 1.27)
        lin = max(lin, float((R - r[on]).max()) if on.any() else 0)
        dm = depth(X[mv], X).max(); mdep = max(mdep, float(dm)); mfr += int(dm > 0.01)
    out[c] = dict(R_fingers_in_shaft_cm=round(max(gin, 0) * 100, 2), R_wrap_deg_median=round(float(np.median(wraps)), 0) if wraps else 0,
                  L_fingers_in_shaft_cm=round(max(lin, 0) * 100, 2), mallet_in_body_cm=round(mdep * 100, 2), mallet_frames_over_1cm=mfr)
    print(f"{c:13s} R fingers in shaft {out[c]['R_fingers_in_shaft_cm']:5.2f} cm, wrap {out[c]['R_wrap_deg_median']:4.0f} deg | L fingers in shaft {out[c]['L_fingers_in_shaft_cm']:5.2f} cm | mallet in body {out[c]['mallet_in_body_cm']:5.2f} cm ({mfr} f > 1 cm)", flush=True)
if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=1)
