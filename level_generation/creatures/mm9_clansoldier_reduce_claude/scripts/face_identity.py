#!/usr/bin/env python3
"""Face skin identity: every installed ClanHead_A triangle of the face/neck skin and eyes (parts 20, 22) must exist in the candidate with
the same corner positions, UVs, normals, joints and weights (1e-6). Usage: face_identity.py <candidate glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb
def head(path):
    g = Glb(path); p = next(p for p in g.json['meshes'][0]['primitives'] if g.json['materials'][p['material']]['name'] == 'ClanHead_A')
    A = {k: np.asarray(g.accessor(v), float) for k, v in p['attributes'].items()}; T = np.asarray(g.accessor(p['indices'])).astype(int).reshape(-1, 3)
    J, Wt = A['JOINTS_0'], A['WEIGHTS_0']; o = np.lexsort((J, -Wt))  # influences as (joint, weight) pairs sorted, zero weights dropped
    JW = np.zeros((len(J), 8))
    for i in range(len(J)):
        pr = sorted((int(j), round(float(w), 4)) for j, w in zip(J[i], Wt[i]) if w > 1e-4); f = [x for q in pr for x in q]; JW[i, :len(f)] = f
    return {k: np.concatenate([A['POSITION'][T], A['TEXCOORD_0'][T]] + ([A['NORMAL'][T]] if k in ('n', 'all') else []) + ([JW[T]] if k in ('w', 'all') else []), 2) for k in ('pos', 'n', 'w', 'all')}, A, T
S, _, _ = head(str(HERE / 'before' / 'mm9_clansoldier.glb')); C, _, _ = head(sys.argv[1])
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part'][g['mat'] == 2]
face = np.isin(part, (20, 22))
from scipy.spatial import cKDTree
def srt(X):   # corners sorted by position so a rotated triangle compares equal
    o = np.lexsort((X[:, :, 2], X[:, :, 1], X[:, :, 0]), axis=1) if False else np.argsort(X[:, :, 0] * 1e6 + X[:, :, 1] * 1e3 + X[:, :, 2], axis=1)
    return np.take_along_axis(X, o[:, :, None], 1)
for k in ('pos', 'n', 'w'):
    A_, B_ = srt(S[k][face]), srt(C[k])
    d, nn = cKDTree(B_[:, :, :3].reshape(len(B_), -1)).query(A_[:, :, :3].reshape(len(A_), -1))
    diff = np.abs(A_ - B_[nn]).max((1, 2))
    print('FACE', k, 'triangles', int(face.sum()), 'max abs diff', float(diff.max()), 'over 1e-5:', int((diff > 1e-5).sum()))
