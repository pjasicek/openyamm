#!/usr/bin/env python3
"""Survey of the installed cat LOD0 for the keep set: components, dominant bones, head-weighted faces by z, edge lengths."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_cat.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Cat' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh'])[0]
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
P, T, J, W = pr['POSITION'].astype(float), pr['T'], pr['JOINTS_0'], pr['WEIGHTS_0'].astype(float)
nF = len(T); print('faces', nF, 'verts', len(P), 'bbox', P.min(0).round(3), P.max(0).round(3))
key = np.round(P, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
nc, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]
fw = np.zeros((nF, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c])
fw /= 3; dom = fw.argmax(1); cen = P[T].mean(1)
el = np.linalg.norm(P[T] - P[T[:, [1, 2, 0]]], axis=2).mean(1)
print('components', nc)
for c in np.argsort(-np.bincount(fl)):
    s = fl == c
    if not s.any(): continue
    bones = np.bincount(dom[s], minlength=len(joints)); top = np.argsort(-bones)[:3]
    print(f'  comp {c}: {int(s.sum())} faces, cen {cen[s].mean(0).round(3)}, z {cen[s,2].min():.3f}..{cen[s,2].max():.3f}, '
          f'y {cen[s,1].min():.3f}..{cen[s,1].max():.3f}, bones {[(joints[t], int(bones[t])) for t in top if bones[t]]}, edge {el[s].mean()*1000:.1f} mm')
import os; H = os.environ['HEAD_BONES'].split(',')
hw = fw[:, [joints.index(n) for n in H]].sum(1)
print('head-weighted > 0.5:', int((hw > .5).sum()))
for n in joints:
    s = dom == joints.index(n)
    if s.sum(): print(f'  dom {n:12s} {int(s.sum()):5d} z {cen[s,2].min():.3f}..{cen[s,2].max():.3f} y {cen[s,1].min():.3f}..{cen[s,1].max():.3f} edge {np.median(el[s])*1000:.1f} mm')
main = np.bincount(fl).argmax(); m = fl == main
for z0 in np.arange(P[:,2].min(), P[:,2].max(), 0.05):
    s = m & (cen[:, 2] > z0) & (cen[:, 2] <= z0 + 0.05)
    print(f'  main z {z0:.2f}-{z0+.05:.2f}: {int(s.sum()):5d} faces, head-w {int((s & (hw>.5)).sum()):5d}, median edge {np.median(el[s])*1000 if s.any() else 0:.1f} mm')
