#!/usr/bin/env python3
"""PF4 hood lining, revised after the paint (2026-11-02; the viewer showed dark patches on the hood beside the cheeks and jaw: the inside of the
lappets above the 2-ring lining, seen through the opening). The lining (a reversed twin 2.5 mm inside the outer hood, sharing its UVs) now
covers every outer hood face of the outer LIN rings that stands off the head (face centre more than HUG from the head shell, F1's old hood
and the bodice), and is dropped where the hood hugs the face (1.5 mm out: a lining 2.5 mm in lies inside the head, never seen).
Applied to the asm AND to work/uv.npz (new rows carry the outer twin's UV; the paid layout and every other row are unchanged), so it runs
once after uv_pf4.py. Faces keep their order apart from the removed linings (later faces shift down; f4_twin_face remapped); new lining
faces and vertices are appended. Args: <asm in> <uv in> <asm out> <uv out> [LIN rings] [HUG m]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
AI, UI, AO, UO = sys.argv[1:5]; LIN = int(sys.argv[5]) if len(sys.argv) > 5 else 5; HUG = float(sys.argv[6]) if len(sys.argv) > 6 else 0.004
A = dict(np.load(AI)); U = dict(np.load(UI))
co, tri, comp = A['co'], A['tri'], A['comp']; names = [str(x) for x in A['names']]
inner, rim, twf, twv, par = A['f4_inner'], A['f4_rim'], A['f4_twin_face'], A['f4_twin_v'], A['f4_param']
K4 = names.index('hood4'); fc = comp[tri[:, 0]]
# ---- the uv row of every asm face (uv_pf4.py: body set faces in ascending order, then head set faces in ascending order)
isf = lambda *n: np.isin(fc, [names.index(x) for x in n])
lining_f = twf >= 0
BODY = (isf('dress', 'skirt', 'lining', 'legs', 'hands', 'sleeve4') & ~lining_f) | (lining_f & isf('sleeve4'))
HEAD = (isf('head', 'scarf', 'hood4') & ~lining_f) | (lining_f & isf('hood4'))
order = np.r_[np.where(BODY)[0], np.where(HEAD)[0]]
assert len(order) == len(U['tri']) == len(tri), (len(order), len(U['tri']), len(tri))
row_of = np.empty(len(tri), int); row_of[order] = np.arange(len(order))
# ---- which outer hood faces want a lining
Kr = par[comp == K4, 2].max()
outer = np.where((fc == K4) & ~inner & ~rim)[0]
ring_f = par[tri[outer], 2].min(1)
used = np.unique(tri)
bodyv = np.intersect1d(np.where(np.isin(comp, [names.index(n) for n in ('head', 'scarf', 'dress')]))[0], used)
gap = cKDTree(co[bodyv]).query(co[tri[outer]].mean(1))[0]
want = outer[(ring_f >= Kr - LIN) & (gap > HUG)]
have = {int(twf[f]): f for f in np.where(lining_f & (fc == K4))[0]}
drop = np.array(sorted(f for o, f in have.items() if o not in set(want.tolist())), int)
add = [o for o in want if int(o) not in have]
# ---- lining vertices: reuse the existing twin of an outer vertex, else a new one 2.5 mm inside along the outer vertex normal
ht = tri[outer]; fn = np.cross(co[ht[:, 1]] - co[ht[:, 0]], co[ht[:, 2]] - co[ht[:, 0]]); vn = np.zeros_like(co)
for c in range(3): np.add.at(vn, ht[:, c], fn)
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
lin_of = {int(twv[v]): int(v) for v in np.where((twv >= 0) & (comp == K4))[0]}
newv = []
def lv(o):
    if o not in lin_of:
        lin_of[o] = len(co) + len(newv); newv.append(o)
    return lin_of[o]
new_faces = [[lv(int(v)) for v in tri[o]][::-1] for o in add]
# ---- asm: drop, append
keep = np.ones(len(tri), bool); keep[drop] = False
newidx = -np.ones(len(tri), int); newidx[keep] = np.arange(keep.sum())
nv = np.array(newv, int)
A['co'] = np.vstack([co, co[nv] - vn[nv] * 0.0025]) if len(nv) else co
A['comp'] = np.r_[comp, np.full(len(nv), K4)]
A['f4_twin_v'] = np.r_[twv, nv]; A['f4_param'] = np.vstack([par, par[nv]]); A['f4_side'] = np.r_[A['f4_side'], np.zeros(len(nv))]
tf2 = np.where(twf[keep] >= 0, newidx[np.maximum(twf[keep], 0)], -1)
A['tri'] = np.vstack([tri[keep], np.array(new_faces, int).reshape(-1, 3)])
A['f4_inner'] = np.r_[inner[keep], np.ones(len(add), bool)]; A['f4_rim'] = np.r_[rim[keep], np.zeros(len(add), bool)]
A['f4_twin_face'] = np.r_[tf2, newidx[np.array(add, int)]] if len(add) else tf2
assert (A['f4_twin_face'][A['f4_twin_face'] >= 0] >= 0).all()
np.savez(AO, **A)
# ---- uv: drop the rows of dropped faces, append new faces with the outer twin's corner UVs (new rows), material 1
ut, uv, uo = U['tri'], U['uv'], U['orig']
ukeep = np.ones(len(ut), bool); ukeep[row_of[drop]] = False
nco, nuv, nor_, ncomp = [], [], [], []; nt = []
base = len(U['co'])
for o, lf in zip(add, new_faces):
    r = row_of[o]; uvo = {int(uo[k]): uv[k] for k in ut[r]}
    row = []
    for v in lf:
        ov = A['f4_twin_v'][v]; row.append(base + len(nco)); nco.append(A['co'][v]); nuv.append(uvo[int(ov)]); nor_.append(v); ncomp.append(K4)
    nt.append(row)
U['tri'] = np.vstack([ut[ukeep], np.array(nt, int).reshape(-1, 3)])
U['co'] = np.vstack([U['co'], np.array(nco).reshape(-1, 3)]); U['uv'] = np.vstack([uv, np.array(nuv).reshape(-1, 2)])
U['orig'] = np.r_[uo, np.array(nor_, int)]; U['comp'] = np.r_[U['comp'], np.array(ncomp, int)]
U['mat'] = np.r_[U['mat'][ukeep], np.ones(len(nt), U['mat'].dtype)]; U['inner'] = np.r_[U['inner'][ukeep], np.ones(len(nt), bool)]
used_r = np.unique(U['tri']); remap = -np.ones(len(U['co']), int); remap[used_r] = np.arange(len(used_r))
for k in ('co', 'uv', 'orig', 'comp'): U[k] = U[k][used_r]
U['tri'] = remap[U['tri']]
np.savez(UO, **U)
print('RELINE added', len(add), 'dropped', len(drop), 'new lining vertices', len(nv), 'tris', len(A['tri']), 'uv rows', len(U['co']))
