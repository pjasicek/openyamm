#!/usr/bin/env python3
"""Is a hand's vertex really inside the other hand's talons? Generalised winding number of each of that side's hand/finger
vertices against every closed talon piece of the other hand (posed), installed vs candidate, at one clip frame.
Usage: talon_inside.py <a.glb> <b.glb> <clip> <frame48> <side of the probed vertices L|R>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
a, b, clip, fr, side = sys.argv[1:6]; other = 'R' if side == 'L' else 'L'
def wn(p, A, B, C):
    a, b, c = A - p, B - p, C - p; la, lb, lc = (np.linalg.norm(x, axis=1) for x in (a, b, c))
    det = np.einsum('ij,ij->i', a, np.cross(b, c)); den = la * lb * lc + np.einsum('ij,ij->i', a, b) * lc + np.einsum('ij,ij->i', b, c) * la + np.einsum('ij,ij->i', c, a) * lb
    return np.arctan2(det, den).sum() / (2 * np.pi)
for f in (a, b):
    g = Glb(Path(f)); m = Model(g); names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
    pr = m.primitives[0]; dom = np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))])
    T = pr['triangles']; P = pr['positions']; _, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.reshape(-1); TT = tp[T]
    n = tp.max() + 1; _, lab = connected_components(coo_matrix((np.ones(3 * len(TT)), (TT.ravel(), np.roll(TT, 1, 1).ravel())), (n, n)), directed=False)
    fl = lab[TT[:, 0]]
    X = m.skinned_positions(m.world(m.sample(clip, int(fr) / 48.0)))[0][0]
    hv = np.where(np.array([f' {side} ' in d and ('Finger' in d or 'Hand' in d) for d in dom]))[0]
    worst = 0
    for c in np.unique(fl):
        fs = T[fl == c]
        if len(fs) > 300 or not all(f' {other} ' in dom[v] for v in fs[:3].ravel()) or not any('Finger' in dom[v] for v in fs.ravel()): continue
        A, B, C = X[fs[:, 0]], X[fs[:, 1]], X[fs[:, 2]]
        w = np.array([wn(X[v], A, B, C) for v in hv]); worst = max(worst, np.abs(w).max())
    print(Path(f).name, clip, fr, side, 'max |winding| of', len(hv), 'hand vertices against the other hand talons:', round(float(worst), 3), '(1 = inside)')
