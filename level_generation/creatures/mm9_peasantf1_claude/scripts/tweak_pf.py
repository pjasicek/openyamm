#!/usr/bin/env python3
"""Geometry tweaks after the paint (UVs unchanged, the paint moves with the mesh): the mirrored head meets itself at x = 0 at an angle, a crease
that shaded as a dark line down the chin and a light strip on the nose. Vertices within BAND of the midline on the face are pulled forward
(depth only, valleys only, at most 3 mm), so the halves meet smoothly; ridges (the nose) are left. Args: <asm npz> <uv_tex npz> <out npz> [band m] [passes]"""
import sys
import numpy as np
A, U, OUT = sys.argv[1:4]; CAP = 0.003; BAND = float(sys.argv[4]) if len(sys.argv) > 4 else 0.010; PASSES = int(sys.argv[5]) if len(sys.argv) > 5 else 8
S = np.load(A); co, tri, comp = S['co'].copy(), S['tri'], S['comp']; names = [str(x) for x in S['names']]
D = dict(np.load(U))
for part in ('head',):
    k = names.index(part); t = tri[comp[tri[:, 0]] == k]
    e = np.unique(np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1), axis=0)
    sel = (comp == k) & (np.abs(co[:, 0]) < BAND) & (co[:, 1] < -0.05)
    mid = (comp == k) & (np.abs(co[:, 0]) < 1e-5)
    w = np.clip(1 - np.abs(co[:, 0]) / BAND, 0, 1)[:, None]
    P = co.copy()
    for _ in range(PASSES):
        acc = np.zeros_like(P); deg = np.zeros(len(P))
        np.add.at(acc, e[:, 0], P[e[:, 1]]); np.add.at(acc, e[:, 1], P[e[:, 0]]); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1)
        L = acc / np.maximum(deg, 1)[:, None]
        dP = (L - P) * 0.5 * w
        dP[:, 0] = 0; dP[:, 2] = 0                                  # depth only, and only where the midline is a valley (moves forward, -y)
        dP[:, 1] = np.minimum(dP[:, 1], 0)
        P[sel] = P[sel] + dP[sel]
        P[sel] = co[sel] + np.clip(P[sel] - co[sel], -CAP, CAP)
        P[mid, 0] = 0
    d = np.linalg.norm(P - co, axis=1); print('TWEAK', part, 'moved', int((d > 1e-5).sum()), 'max mm', round(float(d.max()) * 1000, 2))
    co = P
# slivers: the bisect left vertices a hair off the plane (|x| 0.2-2 mm) whose mirror twins make needle faces with steep normals along the
# midline (the dark line down the chin). Snapped onto x = 0 they become zero-area faces that add nothing to the normals.
SNAP = 0.0025
for part in ('head', 'scarf', 'dress', 'band', 'skirt', 'lining'):
    k = names.index(part); q = (comp == k) & (np.abs(co[:, 0]) < SNAP) & (np.abs(co[:, 0]) > 0)
    co[q, 0] = 0; print('SNAP', part, int(q.sum()))
# hand stubs: the 6 cm cut left a zig-zag rim (pale spikes in the open cuff). The rim goes onto one ring 6 cm behind the wrist, the next rows
# are relaxed along the arm; UVs are unchanged (the stretched skin sits inside the cuff)
from collections import defaultdict
k = names.index('hands'); t = tri[comp[tri[:, 0]] == k]
ec = defaultdict(int)
for a, b, c in t:
    for e in ((a, b), (b, c), (c, a)): ec[(min(e), max(e))] += 1
rim = np.unique([v for e, n in ec.items() if n == 1 for v in e])
e = np.array([e for e in ec]); wr0, ax0 = S['wr'], S['ax']
for sg in (1, -1):
    fd = ax0 * [sg, 1, 1]; w = wr0 * [sg, 1, 1]
    side = (comp == k) & (co[:, 0] * sg > 0)
    al = (co - w) @ fd
    r_ = rim[side[rim]]
    co[r_] += ((-0.06 - al[r_])[:, None]) * fd
    mov = np.where(side & (al < -0.012))[0]; mov = np.setdiff1d(mov, r_)
    for _ in range(6):
        al = (co - w) @ fd; acc = np.zeros(len(co)); deg = np.zeros(len(co))
        np.add.at(acc, e[:, 0], al[e[:, 1]]); np.add.at(acc, e[:, 1], al[e[:, 0]]); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1)
        tgt = acc / np.maximum(deg, 1)
        co[mov] += ((0.5 * (tgt[mov] - al[mov]))[:, None]) * fd
    print('STUB rim', sg, len(r_), 'relaxed', len(mov))
# the cuff's top rim onto the sleeve end it meets (Meshy left a 2-10 mm crack between the two parts, seen from below)
from scipy.spatial import cKDTree
kc = names.index('cuffs'); tc = tri[comp[tri[:, 0]] == kc]; ecc = defaultdict(int)
for a, b, c in tc:
    for e_ in ((a, b), (b, c), (c, a)): ecc[(min(e_), max(e_))] += 1
crim = np.unique([v for e_, n in ecc.items() if n == 1 for v in e_]); dv = np.where(comp == names.index('dress'))[0]
dd, nn = cKDTree(S['co'][dv]).query(S['co'][crim]); m_ = dd < 0.012; co[crim[m_]] = S['co'][dv[nn[m_]]]; print('CUFF rim snapped', int(m_.sum()))
D['co'] = co[D['orig']]
np.savez(OUT, **D); print('saved', OUT)
