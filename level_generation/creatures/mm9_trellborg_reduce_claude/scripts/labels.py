#!/usr/bin/env python3
"""Per-face labels of the welded source (work/mesh_in.npz) from the creature's final rest mesh (work/final_faces.npz, same frame,
centroid match): region per face -> work/labels.npz.
Regions: 1 body skin (Trellborg_A, not hand), 2 hand (f_hand), 3 cuff (part 30), 4 face front (head set inside the creature's own
reduce_trell.py face box), 5 hair (head set above the head plane, outside the face box), 6 neck/shoulder head-set skin (below the
head plane), 7 tusks (part 14), 8 club (part 20).
Also: seam = head-set faces within SEAMR rings of a body-material face (neck seam), junction = hand faces touching a non-hand face
(+ JR rings: the hand-graft junction), soles."""
import os
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
HERE = Path(__file__).resolve().parents[1]
d = np.load(HERE / 'work/mesh_in.npz'); V, F = d['verts'], d['faces']
f = np.load(HERE / 'work/final_faces.npz')
fc = V[F].mean(1); dist, nn = cKDTree(f['co'].mean(1)).query(fc); assert dist.max() < 1e-4
fmat, fhand = f['f_mat'][nn], f['f_hand'][nn]
vpart = f['v_part'][f['tri'][nn]].max(1)
mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
C = np.array([0.0, 0.03, 0.76]); N = np.array([0.0, -0.25, 0.968]); N /= np.linalg.norm(N)
FB = float(os.environ.get('FACE_BOX_Y', -0.015)); FZ = float(os.environ.get('FACE_BOX_Z', 1.03)); FX = float(os.environ.get('FACE_BOX_X', 0.175))
P = V[F]
head = ((P - C) @ N > -0.02).all(1)
face = head & (P[:, :, 1] < FB).any(1) & (P[:, :, 2] < FZ).all(1) & (np.abs(P[:, :, 0]) < FX).all(1)
reg = np.zeros(len(F), int)
reg[(mat == 0)] = 1
reg[(mat == 0) & (fhand > 0)] = 2
reg[vpart == 30] = 3
hs = mat == 1
reg[hs & face] = 4
reg[hs & head & ~face] = 5
reg[hs & ~head] = 6
reg[vpart == 14] = 7
reg[mat == 2] = 8
# face adjacency (shared vertex)
nf = len(F); rows = np.repeat(np.arange(nf), 3); A = coo_matrix((np.ones(3 * nf), (rows, F.reshape(-1))), shape=(nf, len(V))).tocsr()
def grow(sel, rings):
    for _ in range(rings):
        vs = np.zeros(len(V), bool); vs[F[sel].reshape(-1)] = True; sel = sel | vs[F].any(1)
    return sel
SEAMR = int(os.environ.get('SEAMR', 2)); JR = int(os.environ.get('JR', 1))
seam = hs & grow(mat == 0, SEAMR)
junction = (reg == 2) & grow(np.isin(reg, [1]), JR)
sole = P[:, :, 2].min(1) < V[:, 2].min() + 0.02
names = {1: 'body', 2: 'hand', 3: 'cuff', 4: 'face', 5: 'hair', 6: 'neck', 7: 'tusk', 8: 'club'}
print({names[k]: int((reg == k).sum()) for k in names}, 'seam', int(seam.sum()), 'junction', int(junction.sum()), 'sole', int(sole.sum()))
np.savez(HERE / 'work/labels.npz', reg=reg, seam=seam, junction=junction, sole=sole, mat=mat)
