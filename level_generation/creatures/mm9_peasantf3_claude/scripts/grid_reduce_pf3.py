#!/usr/bin/env python3
"""Veil and braids at reduced resolution (VEIL_ROWS x 2 columns, BRAID_RINGS rings per block) (PF3 second pass, 2026-11-02; LOD0 under 15k). Both are regular grids from add_parts_pf3.py (veil:
NV rows x NU columns, outer sheet then lining, plus a rim; braids: rings x NS sides plus two caps), so instead of a general decimation
(which shredded the thin veil slab and flattened the braid tubes) every other veil column and every other braid ring is dropped and the
quads re-joined across them. A merged quad keeps the paid head UVs only if one UV chart holds all four corners (charts = rows joined by
faces in work/uv.npz); otherwise the two original quads stay. Rim quads along the veil's top and bottom rows are merged the same way.
Triangle winding follows the original faces' normals. Args: <asm npz> <uv npz in> <uv npz out>"""
import sys, json
import numpy as np
A = np.load(sys.argv[1]); D = dict(np.load(sys.argv[2]))
names = [str(x) for x in A['names']]; acomp = A['comp']; aco = A['co']
co, tri, uv, orig, mat, comp, inner = D['co'], D['tri'], D['uv'], D['orig'], D['mat'], D['comp'], D['inner']
fc = comp[tri[:, 0]]
# charts: rows joined by faces
par = np.arange(len(co))
def f(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for t in tri:
    r = f(t[0]); par[f(t[1])] = r; par[f(t[2])] = r
chart = np.array([f(i) for i in range(len(co))])
rows_of = {}
for r, o in enumerate(orig): rows_of.setdefault(int(o), {})[int(chart[r])] = r
def common(vs):
    cs = set(rows_of.get(int(vs[0]), {}))
    for v in vs[1:]: cs &= set(rows_of.get(int(v), {}))
    return next(iter(cs)) if cs else None
NU, NV = 23, 14
kv, kb = names.index('veil'), names.index('braids')
vv = np.where(acomp == kv)[0]; v0 = vv.min(); nout = NU * NV
bv = np.where(acomp == kb)[0]; b0 = bv.min(); NS = 7; per = len(bv) // 2; NR = (per - 2) // NS
def nrm(p): return np.cross(p[1] - p[0], p[2] - p[0])
# old faces per part as asm triples (with their normal) to orient the new ones
old = {}
for fi in np.where(np.isin(fc, [kv, kb]))[0]:
    old[tuple(sorted(orig[tri[fi]]))] = fi
def orient(t, ref):
    return t if nrm(aco[list(t)]) @ ref >= 0 else (t[0], t[2], t[1])
def ref_normal(cells):
    n = np.zeros(3)
    for c in cells:
        for fi in c: n += nrm(co[tri[fi]])
    return n
def faces_of_quad(a, b, c, d):
    return [old[k] for k in (tuple(sorted((a, b, c))), tuple(sorted((a, c, d))), tuple(sorted((a, b, d))), tuple(sorted((b, c, d)))) if k in old]
drop = set(); new = []          # new: (asm triple, chart, mat, inner, comp)
stats = {'veil_merged': 0, 'veil_kept': 0, 'braid_merged': 0, 'braid_kept': 0}
def merge_block(corners, cells, part, inn):
    """corners: the merged quad (a, b, c, d); cells: the original quads it replaces. Merged only if every original face is found and one
    UV chart holds all four corners."""
    fs = []
    for q in cells:
        fq = faces_of_quad(*q)
        if len(fq) < 2: return False
        fs += fq
    ch = common(corners)
    if ch is None: return False
    refn = ref_normal([fs]); mt = int(mat[fs[0]]); m = corners
    for t in ((m[0], m[1], m[2]), (m[0], m[2], m[3])):
        new.append((orient(t, refn), ch, mt, inn, part))
    drop.update(fs); return True
def merge(q1, q2, part, inn):
    return merge_block((q1[0], q2[1], q2[2], q1[3]), [q1, q2], part, inn)
vid = lambda i, j, lin=0: v0 + lin * nout + i * NU + j
RS = int(__import__('os').environ.get('VEIL_ROWS', '2')); CS = 2
rows = list(range(0, NV - 1, RS)); rows = rows + [NV - 1] if rows[-1] != NV - 1 else rows
for lin in (0, 1):
    for i0, i1 in zip(rows[:-1], rows[1:]):
        for J in range(0, NU - 2, CS):
            cells = [(vid(i, j, lin), vid(i, j + 1, lin), vid(i + 1, j + 1, lin), vid(i + 1, j, lin)) for i in range(i0, i1) for j in range(J, J + CS)]
            ok = merge_block((vid(i0, J, lin), vid(i0, J + CS, lin), vid(i1, J + CS, lin), vid(i1, J, lin)), cells, kv, bool(lin))
            stats['veil_merged' if ok else 'veil_kept'] += 1
# rim along the top and bottom rows: quads (outer j, outer j+1, lining j+1, lining j)
for i in (0, NV - 1):
    for J in range(0, NU - 2, 2):
        ok = merge((vid(i, J), vid(i, J + 1), vid(i, J + 1, 1), vid(i, J, 1)), (vid(i, J + 1), vid(i, J + 2), vid(i, J + 2, 1), vid(i, J + 1, 1)), kv, False)
        stats['veil_merged' if ok else 'veil_kept'] += 1
for bi in range(2):
    base = b0 + bi * per
    rv = lambda r, k: base + r * NS + (k % NS)
    RB = int(__import__('os').environ.get('BRAID_RINGS', '2'))
    keep = list(range(0, NR, RB)); keep = keep if keep[-1] == NR - 1 else keep + [NR - 1]
    for r1, r2 in zip(keep[:-1], keep[1:]):
        for k in range(NS):
            cells = [(rv(r, k), rv(r + 1, k), rv(r + 1, k + 1), rv(r, k + 1)) for r in range(r1, r2)]
            ok = merge_block((rv(r1, k), rv(r2, k), rv(r2, k + 1), rv(r1, k + 1)), cells, kb, False)
            stats['braid_merged' if ok else 'braid_kept'] += 1
keepf = np.ones(len(tri), bool); keepf[list(drop)] = False
T = [list(t) for t in tri[keepf]]; M = list(mat[keepf]); IN_ = list(inner[keepf])
for t, ch, mt, inn, part in new:
    T.append([rows_of[int(v)][ch] for v in t]); M.append(mt); IN_.append(inn)
T = np.array(T); used = np.unique(T); remap = -np.ones(len(co), np.int64); remap[used] = np.arange(len(used))
D.update(co=co[used], uv=uv[used], orig=orig[used], comp=comp[used], tri=remap[T], mat=np.array(M), inner=np.array(IN_, bool))
np.savez(sys.argv[3], **D)
stats['faces'] = int(len(T)); stats['dropped_old'] = len(drop); stats['new'] = len(new)
print('GRIDREDUCE', json.dumps(stats))
