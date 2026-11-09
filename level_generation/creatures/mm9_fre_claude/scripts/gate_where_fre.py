#!/usr/bin/env python3
"""Where gate_fre.py's hood (cap hem) contact happens: for clip@time, the worst cap vertices (rest position in the asm frame, ring, alpha)
and which body part they press into. Args: <glb> <asm npz> <uv npz> clip@t [clip@t ...]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
M = Model(Glb(sys.argv[1])); A = np.load(sys.argv[2]); U = np.load(sys.argv[3])
names = [str(x) for x in A['names']]; comp = A['comp']; par = A['f4_param']; twin = A['f4_twin_v']
ut, um, uo = U['tri'], U['mat'], U['orig']; rows = []; T0 = []; off = 0
for m in range(len(M.primitives)):
    used = np.unique(ut[um == m]); rows.append(uo[used]); T0.append(M.primitives[m]['triangles'] + off); off += len(used)
rows = np.concatenate(rows); T0 = np.vstack(T0); cp = comp[rows]
allpos = lambda p: np.vstack([a for a, _ in p])
rest = allpos(M.skinned_positions(M.world({})))
K = lambda n: names.index(n)
hood = np.where((cp == K('hood4')) & (twin[rows] < 0) & (rest[:, 1] < 1.53))[0]
body = np.where(np.isin(cp, [K('dress'), K('head')]))[0]
def nrm(pts):
    fn = np.cross(pts[T0[:, 1]] - pts[T0[:, 0]], pts[T0[:, 2]] - pts[T0[:, 0]]); vn = np.zeros_like(pts)
    for c in range(3): np.add.at(vn, T0[:, c], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
def depth(pts):
    vn = nrm(pts); d, j = cKDTree(pts[body]).query(pts[hood]); q = pts[hood] - pts[body][j]
    h = -np.einsum('ij,ij->i', q, vn[body][j]); h[(d >= 0.03) | (h < 0)] = 0; return h, j
R0, _ = depth(rest)
for it in sys.argv[4:]:
    c, t = it.split('@'); p = allpos(M.skinned_positions(M.world(M.sample(c, float(t))))); h, j = depth(p); e = h - R0
    for k in np.argsort(-e)[:6]:
        v = rows[hood[k]]; b = rows[body[j[k]]]
        print(it, 'cm %.1f' % (e[k] * 100), 'cap asm', A['co'][v].round(3), 'ring', int(par[v, 2]), 'al %.0f' % par[v, 1], 'into', names[comp[b]], A['co'][b].round(3))
