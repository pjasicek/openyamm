#!/usr/bin/env python3
"""Per body-face info on the installed LOD0: material class (class map at 7 UV samples, majority), bone-group weights,
membrane two-sheet thickness. Writes work/face_info.npz. Prints summary."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as G
doc, binary = G.read(HERE / 'before' / 'mm9_dragonking.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'DragonKing' and 'mesh' in n)
prims = G.prims(doc, binary, node['mesh'])
names = [doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']]
cls = np.asarray(Image.open(HERE.parent / 'mm9_dragonking_claude' / 'textures' / 'dragonking_material_classes.png'))
pr = prims[0]
P = pr['POSITION'].astype(float); T = pr['T']; U = pr['TEXCOORD_0'].astype(float); J = pr['JOINTS_0']; W = pr['WEIGHTS_0'].astype(float)
B = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float); B /= B.sum(1, keepdims=True)
uv = np.einsum('sk,fkc->fsc', B, U[T])
H, Wd = cls.shape
x = np.clip((uv[..., 0] * Wd).astype(int), 0, Wd - 1); y = np.clip((uv[..., 1] * H).astype(int), 0, H - 1)
c = cls[y, x]
fcls = np.array([np.bincount(r[r > 0], minlength=8).argmax() if (r > 0).any() else 0 for r in c])
print('face classes', dict(zip(*np.unique(fcls, return_counts=True))))
M = np.zeros((len(P), len(names)))
for k in range(4):
    np.add.at(M, (np.arange(len(P)), J[:, k]), W[:, k])
wing = np.array([n.startswith('Y') for n in names])
wv = M[:, wing].sum(1)
mem = fcls == 3
print('membrane faces', int(mem.sum()), 'wing-dominant faces', int((wv[T].mean(1) > 0.5).sum()))
# bones weighting membrane vertices
mv = np.unique(T[mem])
for j in np.argsort(-M[mv].sum(0))[:25]:
    w = M[mv, j]; print(f'  {names[j]:14s} sum {w.sum():8.1f} >0.3 {int((w > .3).sum()):4d} >0.5 {int((w > .5).sum()):4d} >0.75 {int((w > .75).sum()):4d} max {w.max():.2f}')
# membrane sheets: per membrane face centroid, distance along -normal to the nearest membrane face with opposite normal
cen = P[T].mean(1); n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); A = np.linalg.norm(n, axis=1) / 2
n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
mi = np.flatnonzero(mem); tr = cKDTree(cen[mi])
d, q = tr.query(cen[mi], 12)
th = []
for a, (dd, qq) in enumerate(zip(d, q)):
    opp = [(dist) for dist, b in zip(dd, qq) if (n[mi[a]] @ n[mi[b]]) < -0.5]
    th.append(min(opp) if opp else np.inf)
th = np.array(th)
print('membrane opposite-sheet distance p10/50/90', np.percentile(th[np.isfinite(th)], [10, 50, 90]).round(4), 'no opposite in 12-nn', int((~np.isfinite(th)).sum()))
print('membrane area', A[mem].sum().round(2), 'body area', A.sum().round(2), 'height', (P[:, 1].max() - P[:, 1].min()).round(3))
np.savez(HERE / 'work' / 'face_info.npz', fcls=fcls, M=M, names=np.array(names), wing=wing)
