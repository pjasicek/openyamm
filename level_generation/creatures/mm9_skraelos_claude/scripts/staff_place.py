#!/usr/bin/env python3
"""The bone staff: MM9 skins its staff (37 vertices, 1.44 m, radius ~2.5 cm) to FHP R Finger1. Our staff keeps MM9's axis, centre and length
in that bone's frame, carried onto our rest by our R Finger1 (work/body.glb), and is modelled as a long bone: a slim shaft with two knuckle
swellings and knobbed ends (one end a double condyle), mild per-ring noise. Appended to the assembled npz as part 'staff'.
Args: <asm npz> <mm9 npz> <mm9 glb> <body glb> <out npz>"""
import sys, json
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
A_, M_, MG, BG, OUT = sys.argv[1:6]
D = dict(np.load(A_)); M = np.load(M_); jn = [str(x) for x in M['jn']]
def g(p): return np.c_[p[:, 0], p[:, 2], -p[:, 1]]      # Blender -> glTF
def b(p): return np.c_[p[:, 0], -p[:, 2], p[:, 1]]      # glTF -> Blender
def world(path, name):
    m = Model(Glb(path)); nn = [n.get('name') for n in m.glb.json['nodes']]; return m.world({})[nn.index(name)]
F = 'FHP R Finger1'
Wm, Wo = world(MG, F), world(BG, F); T = Wo @ np.linalg.inv(Wm)
q = M['co'][M['W'][:, jn.index(F)] > 0.5]; qg = g(q)
c = qg.mean(0); u = np.linalg.svd(qg - c)[2][0]; t = (qg - c) @ u; L = float(np.ptp(t)); c = c + u * 0.5 * (t.max() + t.min())
c2 = (T @ np.r_[c, 1])[:3]; u2 = T[:3, :3] @ u; u2 /= np.linalg.norm(u2)
v = np.cross(u2, [0, 1, 0]); v /= np.linalg.norm(v); w = np.cross(u2, v)
NS, NR = 8, 46; rng = np.random.default_rng(7)
s = np.linspace(0, 1, NR)
def bump(x, m, wd, h): return h * np.exp(-((x - m) / wd) ** 2)
r = 0.0135 + bump(s, 0.36, 0.035, 0.007) + bump(s, 0.68, 0.035, 0.0065) + bump(s, 0.0, 0.03, 0.013) + bump(s, 1.0, 0.035, 0.016)
r *= 1 + 0.06 * rng.standard_normal(NR).clip(-2, 2)
V = []
for i, si in enumerate(s):
    cc = c2 + u2 * (si - 0.5) * L
    for j in range(NS):
        a = 2 * np.pi * j / NS; sx = 1.0 + (0.45 if si > 0.96 else 0.0) * abs(np.cos(a))   # a double condyle at the far end
        V.append(cc + r[i] * (sx * np.cos(a) * v + np.sin(a) * w))
Tr = []
for i in range(NR - 1):
    for j in range(NS):
        a_, b_ = i * NS + j, i * NS + (j + 1) % NS; Tr += [[a_, b_ + NS, b_], [a_, a_ + NS, b_ + NS]]
V.append(c2 - u2 * 0.5 * L * 1.005); V.append(c2 + u2 * 0.5 * L * 1.005); e0, e1 = len(V) - 2, len(V) - 1
for j in range(NS):
    Tr.append([e0, j, (j + 1) % NS]); Tr.append([e1, (NR - 1) * NS + (j + 1) % NS, (NR - 1) * NS + j])
Vb = b(np.array(V)); Tr = np.array(Tr)
# winding: outward normals (in Blender frame the glTF->Blender change is a proper rotation)
fn = np.cross(Vb[Tr[:, 1]] - Vb[Tr[:, 0]], Vb[Tr[:, 2]] - Vb[Tr[:, 0]]); fc = Vb[Tr].mean(1)
cb = b(c2[None])[0]; ub = b(u2[None])[0]
radial = fc - cb - np.outer((fc - cb) @ ub, ub)
if np.mean(np.sum(fn * radial, 1) > 0) < 0.5: Tr = Tr[:, ::-1]
names = [str(x) for x in D['names']]
if 'staff' in names: raise SystemExit('staff already in ' + A_)
k = len(names); n0 = len(D['co'])
D['co'] = np.vstack([D['co'], Vb]); D['tri'] = np.vstack([D['tri'], Tr + n0]); D['comp'] = np.r_[D['comp'], np.full(len(Vb), k)]
D['names'] = np.array(names + ['staff']); D['hand_piece'] = np.r_[D['hand_piece'], np.full(len(Vb), -100000)]
D['head_label'] = np.r_[D['head_label'], np.full(len(Vb), -1)]
np.savez(OUT, **D)
# where it passes our hand
R = json.load(open(HERE / 'work/rig.json'))
for f, pts in R['fingers'].items():
    p = np.array(pts[1]); d = np.linalg.norm(p - cb - ((p - cb) @ ub) * ub)
    print('FINGER', f, 'joint2 to staff axis', round(float(d), 3))
print('STAFF', len(Vb), len(Tr), 'length', round(L, 3), 'centre', cb.round(3), 'axis', ub.round(3))
