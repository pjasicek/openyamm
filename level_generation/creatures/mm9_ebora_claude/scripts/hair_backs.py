#!/usr/bin/env python3
"""Back sides for the hair (Concubine face and hair fix, 2026-11-01 evening; user: "some spaces in the hair? like holes?").
The hair shell (part 1), the fringe (4) and the side locks (7) are single-sided open sheets. Every renderer culls their
inner side, so past the face's profile the inside of the far side lock and of the shell's front edge vanished: grey
background between the strands at the temple, a lone strand floating beside the cheek, dark edge-on slivers by the far eye.
Every hair face whose inner side is the nearest surface from any of ~100 directions around the head (the torso occludes)
gets a reversed copy pushed 0.5 mm inward along its vertex normal, with the same UVs, weights and part, so the inside
shows the hair paint and the hair reads as one mass. Vertex moves only on new vertices; nothing existing changes.
Args: <mesh npz> <out npz>"""
import sys
import numpy as np
IN, OUT = sys.argv[1:3]
D = dict(np.load(IN)); co, tri, mat, comp = D['co'], D['tri'], D['mat'], D['comp']
mn = [str(x) for x in D['matnames']]; hm = mn.index('EboraHead'); wm = mn.index('EboraWing')
part = comp[tri].max(1)
HAIR = (1, 4, 7)
hair = (mat == hm) & np.isin(part, HAIR)
c = co[tri].mean(1)
occ = (mat != wm) & (c[:, 2] > 0.55)                     # head set and torso/arms above the waist (wings left out)
F = np.where(occ)[0]
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
# outward check: the head's hair normals point away from the skull centre for most faces
ctr = np.array([0.0, 0.05, 0.90]); out_ok = ((c[hair] - ctr) * fn[hair]).sum(1) > 0
print('hair faces', int(hair.sum()), 'outward-facing share %.2f' % out_ok.mean())
R = 700; O = 0.42; C0 = np.array([0.0, 0.04, 0.88])
g = (1 + 5 ** 0.5) / 2; n = 100; k = np.arange(n) + 0.5
dirs = np.c_[np.cos(2 * np.pi * k / g) * np.sqrt(1 - (1 - 2 * k / n) ** 2), np.sin(2 * np.pi * k / g) * np.sqrt(1 - (1 - 2 * k / n) ** 2), 1 - 2 * k / n]
seen = np.zeros(len(tri), bool)
P = co[tri[F]]
for d in dirs:
    up = np.array([0, 0, 1.0]) if abs(d[2]) < 0.95 else np.array([0, 1.0, 0])
    r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
    px = ((P - C0) @ r / O + 0.5) * R; py = (0.5 - (P - C0) @ u / O) * R; dz = (P - C0) @ d
    zb = np.full((R, R), -1e9); idb = np.full((R, R), -1)
    for j in range(len(F)):
        x, y, z = px[j], py[j], dz[j]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), R - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), R - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        det = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(det) < 1e-14: continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / det
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / det
        m = (a >= 0) & (b >= 0) & (1 - a - b >= 0)
        zz = a * z[0] + b * z[1] + (1 - a - b) * z[2]; sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= zz > sub
        sub[m] = zz[m]; idb[y0:y1 + 1, x0:x1 + 1][m] = F[j]
    ids = np.unique(idb[idb >= 0]); back = ids[(fn[ids] @ d) < 0]
    seen[back[hair[back]]] = True
# the shell: only faces whose inner side is ever the nearest surface; the fringe and the side locks are thin cards seen
# from both sides: whole
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
sel = seen | (hair & np.isin(part, (4, 7)))
# no UV fragments: a copied group of fewer than 8 faces on one UV island (connected by shared vertex indices) grows by rings
# of hair faces of the same island up to 8 (texture_quality.py counted the lone copies as fragments: 3.0 % of the head)
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
def groups(mask):
    # edge-connected (texture_quality.py joins two triangles only across a shared edge with the same UVs at both ends)
    f = np.where(mask)[0]; t = tri[f]
    e = np.sort(np.r_[t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]], 1); fi = np.tile(np.arange(len(f)), 3)
    _, ek = np.unique(e, axis=0, return_inverse=True); ek = ek.ravel()
    A = coo_matrix((np.ones(len(fi)), (fi, ek)), shape=(len(f), ek.max() + 1)).tocsr()
    n_, lab = connected_components(A @ A.T, directed=False); return f, lab
for ring in range(6):
    f, lab = groups(sel); sz = np.bincount(lab); small = f[sz[lab] < 8]
    if not len(small): break
    es = set(map(tuple, np.sort(np.r_[tri[small][:, [0, 1]], tri[small][:, [1, 2]], tri[small][:, [2, 0]]], 1)))
    cand = np.where(hair & ~sel)[0]
    add_ = np.zeros(len(tri), bool)
    add_[[c for c in cand if any(tuple(sorted((tri[c][k], tri[c][(k + 1) % 3]))) in es for k in range(3))]] = True
    if not add_.any(): break
    sel = sel | add_
f, lab = groups(sel); sz = np.bincount(lab)
print('copy groups', len(sz), 'under 8 faces', int((sz < 8).sum()), 'faces in them', int(sz[sz < 8].sum()))
print('hair faces with a visible inner side', int(seen.sum()), 'copied', int(sel.sum()),
      {p: int((sel & (part == p)).sum()) for p in HAIR})
# vertex normals of the hair sheets (position-welded within the hair), copies 0.5 mm inward
hv = np.unique(tri[sel]); Nv = np.zeros((inv.max() + 1, 3))
for i in range(3): np.add.at(Nv, inv[tri[hair, i]], fn[hair])
Nv /= np.maximum(np.linalg.norm(Nv, axis=1, keepdims=True), 1e-12)
remap = -np.ones(len(co), int); remap[hv] = len(co) + np.arange(len(hv))
add = {}
for key_ in D:
    a = D[key_]
    if isinstance(a, np.ndarray) and a.ndim >= 1 and len(a) == len(co) and key_ != 'tri':
        add[key_] = a[hv]
add['co'] = co[hv] - Nv[inv[hv]] * 0.0005
if 'orig' in add: add['orig'] = -np.ones(len(hv), D['orig'].dtype)
for key_, a in add.items(): D[key_] = np.concatenate([D[key_], a])
newt = remap[tri[sel]][:, ::-1]
D['tri'] = np.concatenate([tri, newt]); D['mat'] = np.concatenate([mat, mat[sel]])
for key_ in D:
    if isinstance(D[key_], np.ndarray) and len(D[key_]) == len(tri) and key_ not in ('tri', 'mat'):
        D[key_] = np.concatenate([D[key_], D[key_][sel]])
np.savez(OUT, **D)
print('HAIR BACKS', len(newt), 'faces added, total', len(D['tri']))
