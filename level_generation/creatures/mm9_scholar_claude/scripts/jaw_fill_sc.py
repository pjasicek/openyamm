#!/usr/bin/env python3
"""Close the gaps between the face shell and the beard at the jaw sides (review r9, tier B front: two dark blue triangles where the robe
showed between the face's lower edge and the beard). After the paint, geometry added only: each open boundary edge of the head shell in the
jaw zone (ZMIN < z < ZMAX, XMIN < |x| < XMAX, in front: y < YMAX) is extruded DEPTH inward and back (toward the neck axis x = 0, y = YC)
into a strip of two triangles per edge, facing forward; the strip's vertices take the UV of the nearest beard vertex (hair part: each
tier's head colour paints it as that tier's beard) and the weights of the nearest head vertex (rigid on Head).
Args: <asm npz> <uv npz in> <uv npz out>"""
import sys, os
import numpy as np
from collections import defaultdict
from scipy.spatial import cKDTree
A, U, OUT = sys.argv[1:4]
E = lambda k, d: float(os.environ.get(k, d))
ZMIN, ZMAX, XMIN, XMAX, YMAX, DEPTH, YC = E('JF_ZMIN', '0.62'), E('JF_ZMAX', '0.735'), E('JF_XMIN', '0.025'), E('JF_XMAX', '0.10'), E('JF_YMAX', '-0.01'), E('JF_DEPTH', '0.025'), E('JF_YC', '0.0')
S = np.load(A); co, tri, comp = S['co'], S['tri'], S['comp']; names = [str(x) for x in S['names']]
H, HR = names.index('head'), names.index('hair')
D = dict(np.load(U)); uco, utri, uv, orig, mat = D['co'], D['tri'], D['uv'], D['orig'], D['mat']
ht = tri[comp[tri[:, 0]] == H]
ec = defaultdict(list)
for t in ht:
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): ec[(min(a, b), max(a, b))].append((a, b))
key = np.round(co, 5); _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True); inv = inv.ravel(); shared = cnt[inv] > 1
bnd = [v[0] for k, v in ec.items() if len(v) == 1]
def inzone(p): return ZMIN < p[2] < ZMAX and XMIN < abs(p[0]) < XMAX and p[1] < YMAX
sel = [(a, b) for a, b in bnd if inzone(co[a]) and inzone(co[b])]
print('JAW boundary edges', len(sel))
hair_u = np.where(D['comp'] == HR)[0]; kh = cKDTree(uco[hair_u])
head_a = np.where(comp == H)[0]; ka = cKDTree(co[head_a])
P = list(uco); UV = list(uv); O = list(orig); T = list(utri); MAT = list(mat); extra = {k: list(D[k]) for k in ('comp',) if k in D}
newv = {}
def vert(p):
    P.append(p); UV.append(uv[hair_u[kh.query(p)[1]]]); O.append(head_a[ka.query(p)[1]])
    for k in extra: extra[k].append(H)
    return len(P) - 1
def inner(p):
    d = np.array([-p[0], YC - p[1], -0.4 * DEPTH]); d /= np.linalg.norm(d); return p + d * DEPTH
for a, b in sel:
    for v in (a, b):
        if v not in newv: newv[v] = (vert(co[v]), vert(inner(co[v])))
    (a0, a1), (b0, b1) = newv[a], newv[b]
    f1, f2 = [a0, b0, b1], [a0, b1, a1]
    n = np.cross(P[f1[1]] - P[f1[0]], P[f1[2]] - P[f1[0]])
    if n[1] > 0: f1, f2 = f1[::-1], f2[::-1]
    T += [f1, f2]; MAT += [1, 1]
D['co'] = np.array(P); D['uv'] = np.array(UV); D['orig'] = np.array(O); D['tri'] = np.array(T); D['mat'] = np.array(MAT)
if 'inner' in D: D['inner'] = np.r_[D['inner'], np.zeros(len(T) - len(D['inner']), bool)]
for k in extra: D[k] = np.array(extra[k])
np.savez(OUT, **D); print('JAWFILL', 2 * len(sel), 'faces ->', OUT, len(T))
