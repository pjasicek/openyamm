#!/usr/bin/env python3
"""Held-skull hold at rest (after grip_sk.py): per left digit the signed distance of its pieces to the real skull mesh (contact <= 4 mm, inside
< -2 mm), and the skull's clearance from the cloth (robe/hood vertices within 1 cm of the skull's surface, inside its convex hull).
Args: <asm npz> <skull npz>"""
import sys, json
import numpy as np
from scipy.spatial import cKDTree, Delaunay
D = np.load(sys.argv[1]); S = np.load(sys.argv[2]); H = json.load(open('work/held_skull.json')); R = json.load(open('work/rig_asm2.json'))
co, comp = D['co'], D['comp']; names = [str(x) for x in D['names']]; hp = D['hand_piece']; GR = {int(k): v for k, v in R['groups'].items()}
keep = S['label'] != 3; loc = (S['co'] - np.array(H['eye_c'])) * H['scale'] - np.array(H['box_mid'])
P = loc @ np.array(H['R']).T + np.array(H['centre']); t = S['tri']
fn = np.cross(P[t[:, 1]] - P[t[:, 0]], P[t[:, 2]] - P[t[:, 0]]); vn = np.zeros_like(P)
for c in range(3): np.add.at(vn, t[:, c], fn)
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12); ki = np.where(keep)[0]; kd = cKDTree(P[ki]); hull = Delaunay(P[ki])
def sd(q):
    d, i = kd.query(q); j = ki[i]; s = np.sign(np.sum((q - P[j]) * vn[j], 1)); return d * np.where(s == 0, 1, s)
out = {}
for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
    ks = [k for k, g in GR.items() if g.startswith(f)]; m = np.isin(hp, [-k - 1 for k in ks])
    v = sd(co[m]); out[f] = (round(float(v.min()) * 100, 2))
contact = sum(1 for f, v in out.items() if v <= 0.5 and v >= -0.2)
cloth = np.isin(comp, [names.index('robe'), names.index('hood')]); dc, _ = kd.query(co[cloth]); inh = sd(co[cloth]) < 0
sl = cloth & (co[:, 0] < -0.35); dsl, _ = kd.query(co[sl])
print('HOLD cuff gap cm', round(float(dsl.min()) * 100, 1), 'digit min signed cm', out, 'contacts', contact, '| cloth verts inside skull', int(inh.sum()), 'within 1 cm', int((dc < 0.01).sum()))
