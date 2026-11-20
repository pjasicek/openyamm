#!/usr/bin/env python3
"""Terror survey 2: bone tree with face counts and centres; candidate face-zone sizes."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_terror.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Terror' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh'])[0]
jn = doc['skins'][node['skin']]['joints']; joints = [doc['nodes'][j]['name'] for j in jn]
P, T = pr['POSITION'].astype(float), pr['T']
s = np.load(HERE / 'work' / 'survey.npz'); fl, cav, cls, dom = s['fl'], s['cav'], s['cls'], s['dom']
parent = {}
for i, n in enumerate(doc['nodes']):
    for c in n.get('children', []):
        parent[c] = i
def path(j):
    out = []
    while j in parent:
        out.append(doc['nodes'][j]['name']); j = parent[j]
    return '<'.join(out[:4])
cen = P[T].mean(1)
for k, j in enumerate(jn):
    f = dom == k
    if f.any():
        print(f'{path(j):60s} faces {int(f.sum()):5d} cav {int((f & cav).sum()):4d} centre {cen[f].mean(0).round(2)} cls {np.bincount(cls[f], minlength=4)}')
main = fl == np.bincount(fl).argmax()
pieces = ~main
ev = [np.unique(T[fl == c]) for c in np.unique(fl[pieces])]
eyes = [v for v in ev if len(v) > 80 and np.ptp(P[v], 0).max() / np.ptp(P[v], 0).min() < 1.3]
print('eyes', [(P[v].mean(0).round(3), round(float(np.linalg.norm(P[v] - P[v].mean(0), axis=1).mean()), 3)) for v in eyes])
bagv = np.unique(T[cav]); tr = cKDTree(P[bagv])
dl = tr.query(cen)[0]
for L in (0.03, 0.05, 0.08, 0.12):
    print('lip band', L, int((main & ~cav & (dl < L)).sum()))
for R in (1.6, 2.0, 2.5):
    m = np.zeros(len(T), bool)
    for v in eyes:
        c = P[v].mean(0); r = np.linalg.norm(P[v] - c, axis=1).mean()
        m |= np.linalg.norm(cen - c, axis=1) < R * r
    print('eye socket', R, int((main & ~cav & m).sum()))
headb = np.isin(dom, [joints.index(n) for n in ('Bip01 Head', 'Bone35', 'Bone37', 'Bone38')])
for z in (0.0, 0.2, 0.3, 0.4, 0.5):
    print('head/jaw skin z >', z, int((main & ~cav & headb & (cen[:, 2] > z)).sum()), 'of', int((main & ~cav & headb).sum()))
print('soles', int((P[T][:, :, 1].min(1) < P[:, 1].min() + 0.03).sum()))
