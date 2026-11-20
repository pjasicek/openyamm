#!/usr/bin/env python3
"""Exploration: per primitive of LOD0, connected components (welded by position), dominant joints, UV areas, region mask classes.
Usage: analyse.py <glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bglbio as gb
doc, b = gb.read(sys.argv[1])
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantHOF' and 'mesh' in n)
skin = doc['skins'][node['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
for pr in gb.prims(doc, b, node['mesh']):
    P = pr['POSITION'].astype(float); T = pr['T']; U = pr['TEXCOORD_0'].astype(float); J = pr['JOINTS_0']; W = pr['WEIGHTS_0'].astype(float)
    _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
    r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    nc, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
    fl = lab[FT[:, 0]]
    ua = np.abs(np.cross(np.c_[U[T[:, 1]] - U[T[:, 0]], np.zeros(len(T))], np.c_[U[T[:, 2]] - U[T[:, 0]], np.zeros(len(T))])[:, 2]) / 2
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    dj = acc.argmax(1)
    print(pr['material'], 'faces', len(T), 'verts', len(P), 'components', nc, 'zero-UV faces', int((ua < 1e-10).sum()))
    cnt = np.bincount(fl)
    for c in np.argsort(-cnt)[:40]:
        m = fl == c
        cen = P[T[m]].mean((0, 1))
        u, k = np.unique(dj[m], return_counts=True); top = sorted(zip(k, u), reverse=True)[:4]
        print(f'  comp {c:4d} faces {m.sum():5d} zeroUV {int((ua[m] < 1e-10).sum()):5d} cen {cen.round(3)} y {P[T[m]][..., 1].min():.3f}-{P[T[m]][..., 1].max():.3f} joints', [(jn[x], int(y)) for y, x in top])
    print('  remaining small comps', int((cnt[np.argsort(-cnt)[40:]]).sum()) if nc > 40 else 0)
