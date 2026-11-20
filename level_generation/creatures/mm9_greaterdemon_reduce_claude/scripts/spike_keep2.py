#!/usr/bin/env python3
"""Second spike-root lock (g85's detached-parts audit: the left elbow spike (18 tris on Xaelbow) still parted 1.23 cm in
AttackRanged and the central back spike (20 tris on XspineA) 1.15 -> 1.31 cm): body-skin faces within R m of those two
pieces' vertices are kept. Writes work/keep_extra_spike2.npy. Usage: spike_keep2.py [R]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
R = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
doc, b = gb.read(HERE / 'before' / 'mm9_greaterdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'GreaterDemon' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); nB, nW, nH = (len(p['T']) for p in pr)
a = np.load(HERE / 'work' / 'analyse.npz'); s = np.load(HERE / 'work' / 'glb_sets_a.npz')
j = a['joints']; m0 = a['prim'] == 0; comp, cs, dom, cen = a['comp'][m0], a['csize'][m0], a['dom'][m0], a['cen'][m0]
P = pr[0]['POSITION'].astype(float); T = pr[0]['T']
pick = []
for c in np.unique(comp):
    f = comp == c; n = int(cs[f][0]); bone = j[np.bincount(dom[f]).argmax()]; x = cen[f].mean(0)
    if (n == 18 and bone == 'Xaelbow' and x[0] < 0) or (n == 20 and bone == 'XspineA'):
        pick.append(c); print('piece', c, n, bone, x.round(3))
V = np.unique(T[np.isin(comp, pick)])
big = (cs > 300) & ~s['wingbone'][:nB]
d = cKDTree(P[V]).query(P)[0]
keep = big & (d[T] < R).any(1)
print('skin faces kept', int(keep.sum()))
np.save(HERE / 'work' / 'keep_extra_spike2.npy', np.r_[keep, np.zeros(nW + nH, bool)])
