#!/usr/bin/env python3
"""Gap between the knee discs (loose 62/64-face parts on the thighs) and the rest of the body prim in a clip, installed vs
candidate: per disc the max over its vertices of the distance to the nearest body surface sample. Usage: disc_gap.py <glb>... -- clip"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor')); sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb_pose import Glb, Model
import glbio
args = sys.argv[1:]; i = args.index('--'); glbs, clip = args[:i], args[i + 1]
def samples(P, T, step=0.004):
    out = []
    for t in T:
        a, b, c = P[t]; k = int(np.clip(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / step, 1, 60))
        ii, jj = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = ii + jj <= k
        w = np.stack([ii[m], jj[m], k - ii[m] - jj[m]], 1) / k; out.append(w @ P[t])
    return np.concatenate(out)
for g in glbs:
    doc, b, nd, D = glbio.load(g, 'Krohn'); B = D['Krohn']; T = B['T']
    _, w = np.unique(np.round(B['P'], 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
    lab = connected_components(coo_matrix((np.ones(3 * len(T)), (np.r_[FT[:, 0], FT[:, 1], FT[:, 2]], np.r_[FT[:, 1], FT[:, 2], FT[:, 0]])), shape=(n, n)), directed=False)[1][FT[:, 0]]
    sz = np.bincount(lab); discs = [c for c in np.unique(lab) if sz[c] in (62, 64) and B['P'][T[lab == c]].mean((0, 1))[1] < 0.9]
    m = Model(Glb(g)); dur = max(m.clip_times(clip)); res = {c: 0.0 for c in discs}
    for t in np.arange(0, dur + 1e-6, 1 / 30):
        X = m.skinned_positions(m.world(m.sample(clip, float(t))))[0][0]
        for c in discs:
            tree = cKDTree(samples(X, T[lab != c][np.isin(np.arange((lab != c).sum()), np.arange((lab != c).sum()))]))
            v = np.unique(T[lab == c]); res[c] = max(res[c], float(tree.query(X[v])[0].min()))
    print(Path(g).parent.name, clip, {f"disc x{B['P'][T[lab == c]].mean((0, 1))[0]:+.2f}": round(v * 100, 2) for c, v in res.items()}, 'cm (nearest body point, worst frame)')
