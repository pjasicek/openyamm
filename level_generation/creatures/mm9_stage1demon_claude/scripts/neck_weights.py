"""Neck pass: weights of the welded throat (after neck_weld.py). The skull and the jaw in front of the hinge, the horns and the
body skin away from the neck keep their weights; the rest of the head shell (behind the jaw, below and behind the hinge), the
new tube and the skin round the hole (within BODY_FREE of the hole's rim) take a harmonic blend between them: a cotangent
Laplace solve on the welded surface, every bone channel at once, so the throat runs from the jaw through the neck into the
chest without a seam in the weights. Optional CHAIN (env, default 0.5): the middle of the throat also takes MM9's neck chain
(XneckA low, Xheadpiv high), so a lifted head bends the throat over several joints instead of one Spine-to-head blend.
Runs outside Blender on a neck_dump.py npz; neck_apply_weights.py writes the result into the blend.
Args: <dump npz> <out npz>"""
import sys, os, json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
IN, OUT = sys.argv[1:3]
H = np.array([0, -0.654, 0.62]); GAPE = -24.0
JAW_KEEP = H[1] - float(os.environ.get('JAW_FREE', 0.06))          # head shell in front of this keeps its weights
BODY_FREE = float(os.environ.get('BODY_FREE', 0.10))
CHAIN = float(os.environ.get('CHAIN', 0.0))
d = np.load(IN); P, F, pa, nk = d['V'], d['F'], d['part'], d['neck']; n = len(P); assert F.shape[1] == 3
names = [str(x) for x in d['gn']]; gid = {nm: i for i, nm in enumerate(names)}
W = d['W'].astype(float)
for b in ('XneckA', 'Xheadpiv'):
    if b not in gid: gid[b] = len(names); names.append(b); W = np.c_[W, np.zeros(n)]
tube_v = np.zeros(n, bool); tube_v[F[nk == 1].ravel()] = True
skin = (pa == 0) & ~tube_v; head = pa == 10
# the body loop: skin vertices on tube faces; distance of every skin vertex to it
from scipy.spatial import cKDTree
loop_b = skin & np.isin(np.arange(n), F[nk == 1].ravel())
loop_b = np.zeros(n, bool); loop_b[np.intersect1d(F[nk == 1].ravel(), np.nonzero(pa == 0)[0])] = True
loop_b &= ~np.isin(np.arange(n), np.setdiff1d(np.arange(n), np.unique(F[nk == 0].ravel())))   # on an old face too
db = cKDTree(P[loop_b]).query(P)[0]
ang = np.degrees(np.arctan2(P[:, 2] - H[2], -(P[:, 1] - H[1])))
horn = head & (np.abs(P[:, 0]) > 0.14) & (P[:, 2] > 0.58)
keep_head = head & ((P[:, 1] < JAW_KEEP) | ((ang >= GAPE + 6) & (P[:, 1] < H[1])) | horn)
keep_body = skin & (db > BODY_FREE)
# the welded surface of skin + tube + head shell; other parts (teeth, eyes, tongue, armour, shards) are not in the solve
surf = (pa == 0) | (pa == 10) | tube_v
fs = F[surf[F].all(1)]
free = surf & ~keep_head & ~keep_body
print('NECKW free', int(free.sum()), 'keep head', int(keep_head.sum()), 'keep body', int(keep_body.sum()), 'tube verts', int(tube_v.sum()))
# cotangent Laplacian (weights clamped at 0)
def cot(a, b, c):
    u, v = P[a] - P[c], P[b] - P[c]
    return np.einsum('ij,ij->i', u, v) / np.maximum(np.linalg.norm(np.cross(u, v), axis=1), 1e-12)
I, J, Vv = [], [], []
for (i, j, k) in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
    w = np.maximum(0.5 * cot(fs[:, i], fs[:, j], fs[:, k]), 1e-4)
    I += [fs[:, i], fs[:, j]]; J += [fs[:, j], fs[:, i]]; Vv += [w, w]
I, J, Vv = np.concatenate(I), np.concatenate(J), np.concatenate(Vv)
Lw = coo_matrix((Vv, (I, J)), shape=(n, n)).tocsr()
deg = np.asarray(Lw.sum(1)).ravel()
fi = np.nonzero(free)[0]; ci = np.nonzero(surf & ~free)[0]
idx = -np.ones(n, int); idx[fi] = np.arange(len(fi))
A = (coo_matrix((deg[fi], (np.arange(len(fi)), np.arange(len(fi)))), shape=(len(fi), len(fi))) - Lw[fi][:, fi]).tocsc()
Bc = Lw[fi][:, ci]
def solve(X):           # harmonic in the free set with X fixed on the constrained set
    return spsolve(A, Bc @ X[ci])
Wn = W.copy()
Wn[fi] = solve(W)
# u: 0 at the kept body, 1 at the kept head (for the neck chain)
U = np.zeros(n); U[keep_head] = 1.0
u = np.zeros(n); u[ci] = U[ci]; u[fi] = solve(U[:, None])[:, 0] if False else spsolve(A, Bc @ U[ci])
if CHAIN > 0:
    for bone, c0 in (('XneckA', 0.35), ('Xheadpiv', 0.65)):
        bump = np.clip(1 - np.abs(u - c0) / 0.3, 0, 1) * CHAIN
        bump[~free] = 0
        row = np.zeros(len(names)); row[gid[bone]] = 1
        Wn = Wn * (1 - bump[:, None]) + row * bump[:, None]
Wn = np.clip(Wn, 0, None)
order = np.argsort(-Wn, axis=1)
for i in fi:
    keep = order[i, :4]; row = np.zeros(len(names)); row[keep] = Wn[i, keep]; row[row < 0.015] = 0; Wn[i] = row / max(row.sum(), 1e-9)
top = np.argsort(-Wn[fi].sum(0))[:10]
print('NECKW bones in the free set', [(names[j], round(float(Wn[fi, j].sum()), 1)) for j in top])
np.savez(OUT, fi=fi, W=Wn[fi], gn=np.array(names), u=u)
