"""Probe: pair every topological vertex (position, joints, weights) with another of identical joints+weights nearby."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantdm4.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM4' and 'mesh' in n)
prims = bglbio.prims(doc, b, node['mesh'])
g = np.load(HERE / 'work' / 'glb_parts.npz')
for k, pr in enumerate(prims):
    P = pr['POSITION'].astype(float); J = pr['JOINTS_0'].astype(int); W = pr['WEIGHTS_0'].astype(float); T = pr['T']
    UV = pr['TEXCOORD_0'].astype(float)
    m = g['mat'] == k; tiny = g['uvarea'][m] < 0.5
    # sort joint/weight pairs so ordering does not matter
    o = np.argsort(J, 1); Js = np.take_along_axis(J, o, 1); Ws = np.round(np.take_along_axis(W, o, 1), 3)
    Ws[Ws == 0] = 0; Js[Ws == 0] = 0
    wkey = [tuple(a) + tuple(bb) for a, bb in zip(Js, Ws)]
    groups = {}
    for i, kk in enumerate(wkey):
        groups.setdefault(kk, []).append(i)
    pk = np.round(P, 6)
    sizes = []
    pair_d = []
    for kk, ids in groups.items():
        ids = np.array(ids); u = np.unique(pk[ids], axis=0)
        sizes.append(len(u))
    sizes = np.array(sizes)
    print(pr['material'], 'weight classes', len(groups), 'distinct positions per class', np.bincount(np.minimum(sizes, 6)))
    # vertices used by tiny (lining) faces vs other faces
    lv = np.unique(T[tiny]); ov = np.unique(T[~tiny])
    print('  lining verts', len(lv), 'outer verts', len(ov), 'shared', len(np.intersect1d(lv, ov)))
    # for lining verts: nearest outer vertex with the same weight key
    okeys = {}
    for i in ov:
        okeys.setdefault(wkey[i], []).append(i)
    d = []; nocand = 0
    for i in lv:
        c = okeys.get(wkey[i])
        if not c:
            nocand += 1; continue
        dd = np.linalg.norm(P[c] - P[i], axis=1); d.append(dd.min())
    d = np.array(d)
    if len(d):
        print('  lining->outer same-weight nearest mm p50/p90/p99/max', *(np.percentile(d, [50, 90, 99, 100]) * 1000).round(2), 'no candidate', nocand)
