#!/usr/bin/env python3
"""Yrsa (2026-11-05): per-face labels of the installed LOD0 (before/mm9_yrsa.glb, node Yrsa; prims Yrsa (body: dress, sleeves,
sleeve linings + cuff rims, boots) and YrsaHead (head set: head/neck shell, hood + tail, white hair, braids, bead band; and the
grafted MPFB hands with their forearm extensions)) from the final master (work/master_labels.npz = dump_master_labels.py of
../mm9_yrsa_claude/v2/work/sleeves_v2.blend; Blender frame (x, -z, y), floor lift = master min z).
Labels: master `hand` / `head` face flags, connected pieces per prim (welded by position), dominant joint.
Writes work/glb_parts.npz with part codes assigned by scripts/part_rules (printed table first)."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_yrsa.glb', 'Yrsa')
PR = ['Yrsa', 'YrsaHead']
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
m = np.load(HERE / 'work' / 'master_labels.npz'); mc = m['cen'].astype(np.float64); mt = cKDTree(mc)
lift = None
out = dict(mat=[], hand=[], head=[], cen=[], joint=[], comp=[])
for k, name in enumerate(PR):
    P, T, J, W = D[name]['P'], D[name]['T'], D[name]['J'], D[name]['W']
    cen = P[T].mean(1)
    if lift is None:
        lift = mc[:, 2].min() - 0.0  # refine below by nearest match
        cb0 = np.c_[cen[:, 0], -cen[:, 2], cen[:, 1]]
        lift = np.median(mt.query(cb0 + [0, 0, -0.9307])[0]) * 0 - 0.9307
        d, j = mt.query(cb0 + [0, 0, lift]); dz = np.median(mc[j, 2] - (cb0[:, 2] + lift)); lift += dz
    cb = np.c_[cen[:, 0], -cen[:, 2], cen[:, 1] + lift]
    d, j = mt.query(cb)
    print(name, 'match max', d.max(), 'unique', len(np.unique(j)), len(T))
    assert d.max() < 1e-4 and len(np.unique(j)) == len(T), (name, d.max())
    _, inv = np.unique(P.round(6), axis=0, return_inverse=True); inv = inv.ravel(); TT = inv[T]; n = inv.max() + 1
    e = np.concatenate([TT[:, [0, 1]], TT[:, [1, 2]], TT[:, [2, 0]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    fl = lab[TT[:, 0]]
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    dj = acc.argmax(1)
    hd, hn = m['f_head'][j], m['f_hand'][j]
    for c in np.unique(fl):
        s = fl == c; vs = P[np.unique(T[s])]
        uj, cj = np.unique(dj[s], return_counts=True); top = [jn[x] for x in uj[np.argsort(-cj)][:3]]
        uv = D[name]['UV'][np.unique(T[s])]
        print(f'{name} piece {c:3d} tris {s.sum():5d} head {hd[s].sum():5d} hand {hn[s].sum():5d} lo {vs.min(0).round(3)} hi {vs.max(0).round(3)} uv {uv.min(0).round(2)}-{uv.max(0).round(2)} joints {top}')
    out['mat'] += [k] * len(T); out['hand'].append(hn); out['head'].append(hd); out['cen'].append(cen); out['joint'].append(dj)
    out['comp'].append(fl + (0 if k == 0 else 1000))
print('LIFT', lift)
res = {kk: (np.concatenate(v) if kk != 'mat' else np.array(v)) for kk, v in out.items()}
res['jnames'] = np.array(jn); res['voff'] = np.cumsum([0] + [len(D[x]['P']) for x in PR]); res['foff'] = np.cumsum([0] + [len(D[x]['T']) for x in PR])
np.savez(HERE / 'work' / 'glb_raw_labels.npz', **res)

# ---------------------------------------------------------------- part codes (2026-11-05)
# Body prim: 1 bodice + sleeves (outer), 2 sleeve lining (sleeve_lining.py's inner copy: dark-texel faces of lining-only vertices),
# 3 lining rim strips + Meshy's darkened inner sleeve layer (the other dark-texel faces), 5 skirt, 6 boots, 7 belt, 8 chest panel,
# 9 small pieces (necklace beads, buckle bits, the 3-face R cuff bit). Head prim: 0 MPFB hands, 10 forearm extension (hand faces
# dominated by a Forearm joint), 20 face/neck skin (visible skin-colour faces of the head shell), 21 white hair, 22 hood (dark knit),
# 23 eyes + mouth pieces, 24 braids (xpony* dominated), 25 bead band / earrings (small head pieces), 26 hidden head shell
# (skin- or other-coloured faces never seen in the frontal visibility renders: under the hood).
hc = np.load(HERE / 'work' / 'head_classes.npz')['cls']; vis = np.load(HERE / 'work' / 'vis.npz')['cnt']
nb = res['foff'][1]; nf = res['foff'][2]; comp = res['comp']; joint = res['joint']
part = np.full(nf, -1)
Pb, Tb, Jb, Wb, UVb = (D['Yrsa'][k] for k in ('P', 'T', 'J', 'W', 'UV'))
pt = np.ptp(UVb[Tb], axis=1).max(1) < 1e-6
key = np.round(Pb, 6); _, tp = np.unique(key, axis=0, return_inverse=True); tp = tp.ravel()
a = np.zeros(tp.max() + 1, bool); a[tp[Tb[pt].ravel()]] = True; bb = np.zeros(tp.max() + 1, bool); bb[tp[Tb[~pt].ravel()]] = True
only = (a & ~bb)[tp]
lin = pt & only[Tb].all(1)
csz = np.bincount(comp[:nb])
bp = np.select([lin, pt, comp[:nb] == 0, comp[:nb] == 1, np.isin(comp[:nb], (2, 23)), comp[:nb] == 3, np.isin(comp[:nb], (4, 5))],
               [2, 3, 1, 5, 6, 7, 8], 9)
part[:nb] = bp
hcomp = comp[nb:] - 1000; hj = joint[nb:]
hp = np.full(nf - nb, 26)
big = np.bincount(hcomp).argmax()
isbig = hcomp == big
hp[isbig & (hc == 0) & (vis[nb:] > 0)] = 20
hp[isbig & (hc == 1)] = 21
hp[isbig & (hc == 2)] = 22
hp[isbig & (hc == 3) & (vis[nb:] > 0)] = 20
pony = np.array(['pony' in str(x) for x in jn])
hp[pony[hj] & (hcomp != big) | (pony[hj] & isbig & (hp != 20))] = 24
hp[~isbig] = 23   # every other head piece: eyes, mouth, neck ring, braid ends, bead band, earrings (all kept exact)
hp[hc == 9] = 0
fa = np.array(['Forearm' in str(x) for x in jn])
hp[(hc == 9) & fa[hj]] = 10
part[nb:] = hp
res['part'] = part
# lining twins: per lining vertex the outer body vertex with identical joints/weights 1-5 mm away (sleeve_lining.py offset 3 mm)
from scipy.spatial import cKDTree as KD
lv = np.unique(Tb[lin].ravel()); ov = np.unique(Tb[(bp == 1)].ravel())
tr = KD(Pb[lv]); twin_b = -np.ones(len(Pb), np.int64)
for o in ov:
    ds, js = tr.query(Pb[o], k=8, distance_upper_bound=0.0045)
    for dd, jj in zip(ds, js):
        if not np.isfinite(dd):
            break
        v = lv[jj]
        if dd > 0.0015 and (Jb[o] == Jb[v]).all() and np.abs(Wb[o] - Wb[v]).max() < 1e-6:
            twin_b[o] = v; break
print('lining verts', len(lv), 'outer verts twinned', int((twin_b >= 0).sum()), 'lining verts reached', len(np.unique(twin_b[twin_b >= 0])))
# lining face -> outer face whose twins are its corners (reversed)
fmap = {}
for f in np.flatnonzero(bp == 1):
    t = twin_b[Tb[f]]
    if (t >= 0).all():
        fmap[tuple(sorted(t.tolist()))] = f
pair = -np.ones(nf, np.int64); lined = np.zeros(nf, bool); lining = np.zeros(nf, bool)
miss = 0
for f in np.flatnonzero(lin):
    o = fmap.get(tuple(sorted(Tb[f].tolist())))
    if o is None:
        miss += 1; continue
    pair[o] = f; lined[o] = True; lining[f] = True
print('lining faces', int(lin.sum()), 'paired', int(lining.sum()), 'unpaired', miss)
twin = -np.ones(res['voff'][-1], np.int64); twin[:len(Pb)] = twin_b
res.update(pair=pair, lined=lined, lining=lining, twin=twin, ambig=np.zeros(res['voff'][-1], bool), unmatched=np.zeros(nf, bool))
for p_ in np.unique(part):
    print('part', p_, int((part == p_).sum()))
np.savez(HERE / 'work' / 'glb_parts.npz', **res)
