#!/usr/bin/env python3
"""Inner sleeve caps (viewer Fidget 1.96 s: looking into the bell sleeve showed its empty dark inside and the cut end of the grafted forearm
stub). After the paint, geometry added only (existing faces, UVs and weights unchanged): in each sleeve, DEPTH up the arm from MM9's wrist, a
disc across the sleeve's section (radius = the section loop's mean radius x RK), facing the cuff opening, a fan of N triangles. Its vertices
take the weights of the nearest sleeve vertex on the forearm side (`orig`) and one dark UV of the sleeve's inner cloth (the darkest robe texel near the cuff), so it
reads as the sleeve's shadowed inside; the stub's cut end lies behind it.
Args: <asm npz> <uv npz in> <uv npz out>"""
import sys, os
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshlib import section, nearest_loop
A, U, OUT = sys.argv[1:4]
DEPTH, RK, N = float(os.environ.get('CAP_DEPTH', '0.075')), float(os.environ.get('CAP_RK', '0.85')), 16      # RK 0.97 let the disc's rim cross the flattened sleeve wall (see-through r2: 100-145 px); a two-sided disc fooled the arm gate
S = np.load(A); co, tri, comp = S['co'], S['tri'], S['comp']; names = [str(x) for x in S['names']]
R = names.index('robe'); wr, ax = S['wr'], S['ax']
D = dict(np.load(U)); uco, utri, uv, orig, mat = D['co'], D['tri'], D['uv'], D['orig'], D['mat']
rt = tri[comp[tri[:, 0]] == R]
tex = np.asarray(Image.open('textures/sc_body_tone.png' if os.path.exists('textures/sc_body_tone.png') else 'textures/sc_body_final.png').convert('L'), np.float32)
P = list(uco); UV = list(uv); O = list(orig); T = list(utri); MAT = list(mat); extra = {k: list(D[k]) for k in ('comp',) if k in D}
robe_u = np.where(D['comp'] == R)[0] if 'comp' in D else np.arange(len(uco))
kd = cKDTree(uco[robe_u])
for sg in (1, -1):
    a = ax * [sg, 1, 1]; c0 = wr * [sg, 1, 1] - a * DEPTH
    loop = nearest_loop(section(co, rt, c0, a), c0)
    r = float(np.linalg.norm(loop['pts'] - loop['c'], axis=1).mean()) * RK; c = loop['c']
    u_ = np.cross(a, [0, 0, 1.0]); u_ /= np.linalg.norm(u_); v_ = np.cross(a, u_)
    ring = [c + r * (np.cos(t) * u_ + np.sin(t) * v_) for t in np.linspace(0, 2 * np.pi, N, endpoint=False)]
    # dark UV: the darkest robe texel among the uv vertices within 6 cm of the cuff
    near = robe_u[np.linalg.norm(uco[robe_u] - wr * [sg, 1, 1], axis=1) < 0.06]
    px = (uv[near] * [tex.shape[1] - 1, -(tex.shape[0] - 1)] + [0, tex.shape[0] - 1]).astype(int)
    dk = near[np.argmin(tex[np.clip(px[:, 1], 0, tex.shape[0] - 1), np.clip(px[:, 0], 0, tex.shape[1] - 1)])]
    # weights: the nearest sleeve vertex past the elbow (outer forearm part of the sleeve), never the torso or the inner sleeve wall near it
    sl = robe_u[(uco[robe_u] - c0) @ a > -0.06]; sl = sl[uco[sl, 0] * sg > 0.3]; kds = cKDTree(uco[sl])
    base = len(P)
    for p in [c] + ring:
        P.append(p); UV.append(uv[dk]); O.append(orig[sl[kds.query(p)[1]]])
        for k in extra: extra[k].append(R)
    for i in range(N):
        f = [base, base + 1 + i, base + 1 + (i + 1) % N]
        n = np.cross(P[f[1]] - P[f[0]], P[f[2]] - P[f[0]])
        T.append(f if n @ a > 0 else f[::-1]); MAT.append(0)
    print('CAP', 'R' if sg > 0 else 'L', 'centre', c.round(3), 'radius', round(r, 3))
D['co'] = np.array(P); D['uv'] = np.array(UV); D['orig'] = np.array(O); D['tri'] = np.array(T); D['mat'] = np.array(MAT)
if 'inner' in D: D['inner'] = np.r_[D['inner'], np.ones(len(T) - len(D['inner']), bool)]
for k in extra: D[k] = np.array(extra[k])
np.savez(OUT, **D); print('CAPPED', OUT, len(T))
