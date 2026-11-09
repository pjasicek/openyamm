#!/usr/bin/env python3
"""Faces of the Malevolent Boulder that no camera can see: buried inside another stone in every sampled frame of
every clip (work/posed_verts.npz, every 2nd frame). The model is 122 separate stones that overlap; a stone's faces
inside a neighbour are drawn but always hidden. Removing them changes no pixel and no silhouette. A face counts as
buried when 10 points on it (its corners and edge midpoints pulled 2 % towards the centre, the centre, and three
interior points), and the same points 5 mm out along the face normal (so a face grazing the crevice where two
stones meet stays), all have a generalized winding number above 0.5 for one other stone, frame by frame (the
enclosing stone may differ per frame). Stones with open edges never count as enclosing (two at the back of the cap
have small holes). Same-bone stones move rigidly together, so their buried faces stay buried by
construction; the frame test also admits faces buried by stones on other bones (cap, jaw, base) in every pose.
-> work/hidden.npy (bool per face, dump_mesh.py order).
Usage: hidden_faces.py"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; n = len(v)
W = np.load('work/src_weights.npz')['weights']; bone = W.argmax(1)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; npc = lab.max() + 1
u, cnt = np.unique(np.sort(e, 1), axis=0, return_counts=True)
closed = np.setdiff1d(np.arange(npc), lab[u[cnt == 1][:, 0]])   # an open stone cannot enclose (winding is unreliable)
B = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [.5, .5, 0], [0, .5, .5], [.5, 0, .5], [1 / 3] * 3,
              [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
B = 0.98 * B + 0.02 / 3                          # pulled 2 % towards the centre
DEPTH = 0.005                                    # samples 5 mm out along the face normal must be inside too


def winding(P, tris):
    a = tris[None, :, 0] - P[:, None]; b = tris[None, :, 1] - P[:, None]; c = tris[None, :, 2] - P[:, None]
    la, lb, lc = (np.linalg.norm(x, axis=2) for x in (a, b, c))
    det = np.einsum('mki,mki->mk', a, np.cross(b, c))
    den = (la * lb * lc + np.einsum('mki,mki->mk', a, b) * lc + np.einsum('mki,mki->mk', b, c) * la
           + np.einsum('mki,mki->mk', c, a) * lb)
    return (2 * np.arctan2(det, den)).sum(1) / (4 * np.pi)


def buried(V, faces):
    """bool per face in `faces`: all samples inside one other stone (posed vertices V)"""
    T = V[f[faces]]; nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    S = np.einsum('sk,fkd->fsd', B, T); S = np.concatenate([S, S + DEPTH * nrm[:, None]], 1)
    out = np.zeros(len(faces), bool)
    for c in closed:
        tris = V[f[fl == c]]; lo = tris.reshape(-1, 3).min(0); hi = tris.reshape(-1, 3).max(0)
        cand = np.where(~out & (fl[faces] != c) & np.all((S >= lo) & (S <= hi), axis=(1, 2)))[0]
        if len(cand):
            w = winding(S[cand].reshape(-1, 3), tris).reshape(len(cand), -1)
            out[cand[np.all(w > 0.5, 1)]] = True
    return out


rest = buried(v, np.arange(len(f)))
alive = np.where(rest)[0]
pv = np.load('work/posed_verts.npz'); P, labels = pv['P'], pv['labels']
for k, V in enumerate(P):
    keep = buried(V.astype(np.float64), alive)
    alive = alive[keep]
hidden = np.zeros(len(f), bool); hidden[alive] = True
print('HIDDEN rest', int(rest.sum()), 'every frame', int(hidden.sum()), 'of', len(f), 'faces over', len(P), 'frames')
pieces_touched = len(np.unique(fl[hidden])); print('stones with removed faces', pieces_touched)
np.save('work/hidden.npy', hidden)
