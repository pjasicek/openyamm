#!/usr/bin/env python3
"""Veil lining UVs, corrected per face (2026-11-02): uv_pf3.py gave each lining vertex one UV of its outer twin, so lining triangles at a UV
seam of the outer sheet spanned two charts and covered unrelated texels (the face). Each lining face now takes the UVs of its own outer
twin face's corners (asm: the lining faces follow the outer faces in the same order, corners reversed; lining vertex = outer + n_out).
Only lining rows change; every other row and face of work/uv.npz (the paid head layout) is untouched. Unused rows are dropped.
Args: <asm npz> <uv npz in> <uv npz out>"""
import sys
import numpy as np
A = np.load(sys.argv[1]); U = dict(np.load(sys.argv[2]))
names = [str(x) for x in A['names']]; acomp = A['comp']; atri = A['tri']; inner3 = A['f3_inner']
kv = names.index('veil'); HEAD = [names.index(n) for n in ('head', 'ears', 'scarf', 'veil', 'braids') if n in names]
hf_all = np.where(np.isin(acomp[atri[:, 0]], HEAD))[0]          # uv_pf3.py emitted the head faces in ascending asm order
mat = U['mat']; hrows = np.where(mat == 1)[0]
assert len(hf_all) == len(hrows), (len(hf_all), len(hrows))
row_of = dict(zip(hf_all.tolist(), hrows.tolist()))
vv = np.where(acomp == kv)[0]; par = A['f3_param'][vv]; n_out = next(i for i in range(2, len(par)) if np.allclose(par[i], par[0]))
vf = np.where(acomp[atri[:, 0]] == kv)[0]; lin = vf[inner3[vf]]; outer = vf[~inner3[vf]]
nF = len(lin); f0 = vf.min()
co, uv, orig, comp, tri = list(U['co']), list(U['uv']), list(U['orig']), list(U['comp']), U['tri'].copy()
key = {}
fixed = 0
for fl in lin:
    fo = fl - nF
    assert not inner3[fo] and acomp[atri[fo, 0]] == kv
    ro = row_of[int(fo)]; ocorner = {int(U['orig'][r]): U['uv'][r] for r in tri[ro]}
    rl = row_of[int(fl)]; new = []
    for vl in atri[fl]:
        u_ = ocorner[int(vl) - n_out]; k = (int(vl), round(float(u_[0]), 7), round(float(u_[1]), 7))
        if k not in key:
            key[k] = len(co); co.append(A['co'][vl]); uv.append(u_); orig.append(int(vl)); comp.append(kv)
        new.append(key[k])
    tri[rl] = new; fixed += 1
co, uv, orig, comp = np.array(co), np.array(uv), np.array(orig), np.array(comp)
used = np.unique(tri); remap = -np.ones(len(co), int); remap[used] = np.arange(len(used))
U.update(co=co[used], uv=uv[used], orig=orig[used], comp=comp[used], tri=remap[tri])
np.savez(sys.argv[3], **U)
t = U['uv'][U['tri']]; a = np.abs((t[:, 1, 0] - t[:, 0, 0]) * (t[:, 2, 1] - t[:, 0, 1]) - (t[:, 2, 0] - t[:, 0, 0]) * (t[:, 1, 1] - t[:, 0, 1])) / 2
print('LINING faces fixed', fixed, 'rows', len(used), 'max lining UV area (texels at 1K)', round(float(a[np.where(U['inner'] & (U['mat'] == 1))[0]].max() * 1024 * 1024), 2))
