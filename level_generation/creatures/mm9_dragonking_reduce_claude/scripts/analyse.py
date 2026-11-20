#!/usr/bin/env python3
"""Dragon King body primitive: connected parts (welded by position), dominant bone group per part, wing/membrane faces."""
import sys, json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as G
doc, binary = G.read(HERE / 'before' / 'mm9_dragonking.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'DragonKing' and 'mesh' in n)
prims = G.prims(doc, binary, node['mesh'])
names = [doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']]
def grp(n):
    if n.startswith('Y'): return 'wing'
    if 'tail' in n: return 'tail'
    if n.startswith('Xarm') or n.startswith('Xelbow') or n.startswith('Xankle') or n.startswith('Xfoot') or n.startswith('Xt'): return 'foreleg'
    if n.startswith('Xleg') or n.startswith('Xknee') or n.startswith('Xbankle') or n.startswith('Xfootpiv') or n.startswith('Xbtoe'): return 'hindleg'
    if 'neck' in n or 'head' in n.lower() or 'jaw' in n or 'fin' in n or 'tong' in n: return 'head'
    return 'core'
groups = sorted({grp(n) for n in names})
for pr in prims:
    P = pr['POSITION'].astype(float); T = pr['T']; J = pr['JOINTS_0']; W = pr['WEIGHTS_0'].astype(float)
    _, pk = np.unique(np.round(P, 6), axis=0, return_inverse=True); pk = pk.reshape(-1)
    TF = pk[T]; nV = pk.max() + 1
    r = np.r_[TF[:, 0], TF[:, 1], TF[:, 2]]; c = np.r_[TF[:, 1], TF[:, 2], TF[:, 0]]
    nc, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(nV, nV)), directed=False)
    flab = lab[TF[:, 0]]
    GW = np.zeros((len(P), len(groups)))
    for k in range(4):
        for gi, g in enumerate(groups):
            m = np.array([grp(names[j]) == g for j in J[:, k]])
            GW[m, gi] += W[m, k]
    fg = GW[T].mean(1)
    print(pr['material'], 'faces', len(T), 'verts', len(P), 'topo', nV, 'parts', nc)
    sizes = np.bincount(flab)
    order = np.argsort(-sizes)
    print('  parts by size (faces, dominant group, bbox):')
    agg = {}
    for p in order:
        f = flab == p; g = groups[int(fg[f].mean(0).argmax())]
        agg.setdefault(g, [0, 0]); agg[g][0] += 1; agg[g][1] += int(f.sum())
        if sizes[p] >= 60:
            v = np.unique(T[f]); bb = P[v].max(0) - P[v].min(0)
            print(f'   part {p}: {sizes[p]} faces, {g}, bbox {bb.round(2)}')
    print('  parts per group (count, faces):', agg)
    fdom = np.array(groups)[fg.argmax(1)]
    print('  faces by dominant group:', dict(zip(*np.unique(fdom, return_counts=True))))
    # edges: open / nonmanifold
    E = np.sort(np.r_[TF[:, [0, 1]], TF[:, [1, 2]], TF[:, [2, 0]]], 1)
    _, cnt = np.unique(E, axis=0, return_counts=True)
    print('  edges open', int((cnt == 1).sum()), 'nonmanifold', int((cnt > 2).sum()))
