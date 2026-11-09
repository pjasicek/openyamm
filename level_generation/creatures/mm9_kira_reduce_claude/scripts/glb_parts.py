#!/usr/bin/env python3
"""Kira (2026-11-05): per-face labels of the installed LOD0 (before/mm9_kira.glb, node Kira; prims Kira (body set: armour,
legs, skirt, plates, MPFB hands) and KiraHead (face and neck skin, hair, eyes, braid)) from Kira's final master
(work/master_labels.npz = dump_master_labels.py of ../mm9_kira_claude/work/uv_v6.blend): every GLB triangle's centroid
matches one master face 1:1 (Blender frame (x, -z, y), floor lift 0.9027 m; max 0.011 mm).
Parts: 0 MPFB hands (glove stub inside the vambrace included), 1 armour shell (cuirass, sleeves, vambraces, wrist rim caps),
5 legs and boots, 7 mail skirt, 9 belt, 10 medallion, 11 knee cops, 12 pauldron lames, 13 tasset, 20 face and neck skin,
21 hair, 22 eyes, 23 braid. Writes work/glb_parts.npz (the PeasantM1 project's format; no linings on this model)."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_kira.glb', 'Kira')
PR = ['Kira', 'KiraHead']
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
m = np.load(HERE / 'work' / 'master_labels.npz'); mt = cKDTree(m['cen'].astype(np.float64))
out = dict(mat=[], part=[], cen=[], joint=[], comp=[])
for k, name in enumerate(PR):
    P, T, J, W = D[name]['P'], D[name]['T'], D[name]['J'], D[name]['W']
    cen = P[T].mean(1); cb = np.c_[cen[:, 0], -cen[:, 2], cen[:, 1] - 0.9027]
    d, j = mt.query(cb)
    assert d.max() < 1e-4 and len(np.unique(j)) == len(T) and (m['f_mat'][j] == k).all(), (name, d.max())
    part = m['f_part'][j].astype(int)
    _, inv = np.unique(P.round(6), axis=0, return_inverse=True); inv = inv.ravel(); TT = inv[T]; n = inv.max() + 1
    e = np.concatenate([TT[:, [0, 1]], TT[:, [1, 2]], TT[:, [2, 0]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    fl = lab[TT[:, 0]]
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    dj = acc.argmax(1)
    for c in np.unique(fl):
        s = fl == c; vs = P[np.unique(T[s])]
        u, cnt = np.unique(part[s], return_counts=True)
        print(f'{name} piece {c:3d} tris {s.sum():5d} parts {dict(zip(u.tolist(), cnt.tolist()))} lo {vs.min(0).round(3)} hi {vs.max(0).round(3)}')
    out['mat'] += [k] * len(T); out['part'].append(part); out['cen'].append(cen); out['joint'].append(dj)
    out['comp'].append(fl + (0 if k == 0 else 1000))
res = {kk: (np.concatenate(v) if kk != 'mat' else np.array(v)) for kk, v in out.items()}
nf = len(res['mat'])
res.update(jnames=np.array(jn), lining=np.zeros(nf, int), lined=np.zeros(nf, bool), pair=-np.ones(nf, np.int64),
           unmatched=np.zeros(nf, bool), voff=np.cumsum([0] + [len(D[x]['P']) for x in PR]),
           foff=np.cumsum([0] + [len(D[x]['T']) for x in PR]))
res['twin'] = -np.ones(res['voff'][-1], np.int64); res['ambig'] = np.zeros(res['voff'][-1], bool)
for p in np.unique(res['part']):
    print('part', p, int((res['part'] == p).sum()), 'prims', np.unique(res['mat'][res['part'] == p]).tolist())
np.savez(HERE / 'work' / 'glb_parts.npz', **res)
