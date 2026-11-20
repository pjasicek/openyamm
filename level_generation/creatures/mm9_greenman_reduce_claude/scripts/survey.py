#!/usr/bin/env python3
"""Survey of the installed Green Man LOD0: per primitive the welded connected components (by rounded position) with face count,
size, dominant joint and open-edge share; writes work/survey.npz (per GLB face: mat, comp, comp_size, joint)."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_greenman.glb', 'GreenMan')
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
res = dict(mat=[], comp=[], csize=[], joint=[])
cbase = 0
for k, (name, d) in enumerate(D.items()):
    P, T, J, W = d['P'], d['T'], d['J'], d['W']
    _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; nw = w.max() + 1
    rr = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; cc = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    nc, lab = connected_components(coo_matrix((np.ones(len(rr)), (rr, cc)), shape=(nw, nw)), directed=False)
    fl = lab[FT[:, 0]]
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    fj = acc.argmax(1)
    # edges
    E = np.sort(np.r_[FT[:, [0, 1]], FT[:, [1, 2]], FT[:, [2, 0]]], 1)
    eu, ec = np.unique(E, axis=0, return_counts=True)
    openv = np.zeros(nw, bool); openv[eu[ec == 1].ravel()] = True
    sizes = np.bincount(fl, minlength=nc)
    print(f'== {name}: {len(T)} faces, {len(P)} glb verts, {nw} welded, {nc} components, open-edge verts {openv.sum()} ({openv.mean()*100:.0f} %)')
    hist = [(1, 2), (3, 6), (7, 14), (15, 40), (41, 200), (201, 10 ** 6)]
    for lo, hi in hist:
        m = (sizes >= lo) & (sizes <= hi)
        print(f'   comps {lo}-{hi} faces: {m.sum()} comps, {sizes[m].sum()} faces')
    big = np.argsort(-sizes)[:25]
    for c in big:
        fm = fl == c; vs = np.unique(FT[fm]); pp = P[T[fm]].reshape(-1, 3)
        jj = np.bincount(fj[fm], minlength=len(jn)); top = np.argsort(-jj)[:3]
        print(f'   comp {c}: {sizes[c]} faces, open {openv[vs].mean()*100:.0f} %, y {pp[:,1].min():.2f}-{pp[:,1].max():.2f} '
              f'x {pp[:,0].min():.2f}-{pp[:,0].max():.2f} z {pp[:,2].min():.2f}-{pp[:,2].max():.2f} joints',
              [(jn[t], int(jj[t])) for t in top if jj[t]])
    # small-parts dominant joints
    sm = sizes[fl] <= 40
    jj = np.bincount(fj[sm], minlength=len(jn)); top = np.argsort(-jj)[:12]
    print('   small (<=40) comps by joint', [(jn[t], int(jj[t])) for t in top if jj[t]])
    res['mat'].append(np.full(len(T), k)); res['comp'].append(fl + cbase); res['csize'].append(sizes[fl]); res['joint'].append(fj)
    cbase += nc
np.savez(HERE / 'work' / 'survey.npz', **{k: np.concatenate(v) for k, v in res.items()}, jnames=np.array(jn))
