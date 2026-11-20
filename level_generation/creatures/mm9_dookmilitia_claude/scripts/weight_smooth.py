#!/usr/bin/env python3
"""Skin weight smoothing in joint zones (run 2, collapse gate): the neck and hood seam, the throat under the chin, the mantle at the
clavicles. Vertices are welded by position across primitives (the head and torso materials meet at the collar), so a seam
keeps one weight. A vertex takes part in a zone when the zone's joints hold at least LO of its weight and it lies in the
zone's height band (rest, metres); every other vertex is a fixed boundary. Each pass: w = (1 - A) w + A * mean of the
neighbours, then the zone's weight is kept on the zone's joints (only the split between them moves), the top 4 kept and
renormalised. Islands of under 60 vertices (cheek bars, studs) are left alone. Writes only JOINTS_0/WEIGHTS_0 accessors.
Args: <in glb> <out glb> [zone ...]   zone = name:joint|joint|...:ymin:ymax:passes[:A[:xmax]]"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView
args = sys.argv[1:]; KEEP = []
while '--keep' in args:      # --keep y0,y1,ax0,ax1,z0,z1: rest box (|x| for x) whose vertices no zone moves (the hood hem hangs from the neck by design)
    i = args.index('--keep'); KEEP.append([float(v) for v in args[i + 1].split(',')]); del args[i:i + 2]
src, dst, *zones = args
g = GLTF2().load(src); blob = bytearray(g.binary_blob())
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    dt = {5121: 'u1', 5123: 'u2', 5125: 'u4', 5126: 'f4'}[a.componentType]
    return np.frombuffer(bytes(blob), dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()
def put(arr, ctype, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=ctype, count=len(arr), type=typ))
    return len(g.accessors) - 1
names = [g.nodes[j].name for j in g.skins[0].joints]; NJ = len(names)
mesh = g.meshes[0]; prims = mesh.primitives
P, F, Wd, off = [], [], [], 0
for p in prims:
    pos = acc(p.attributes.POSITION); J = acc(p.attributes.JOINTS_0).astype(int); W = acc(p.attributes.WEIGHTS_0).astype(np.float64)
    D = np.zeros((len(pos), NJ)); np.add.at(D, (np.repeat(np.arange(len(pos)), 4), J.ravel()), W.ravel())
    P.append(pos); Wd.append(D); F.append(acc(p.indices).reshape(-1, 3).astype(int) + off); off += len(pos)
P = np.vstack(P); D = np.vstack(Wd); F = np.vstack(F)
key = np.round(P / 1e-5).astype(np.int64); _, wid, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True); wid = wid.ravel()
nU = wid.max() + 1
DU = np.zeros((nU, NJ)); np.add.at(DU, wid, D); DU /= np.bincount(wid, minlength=nU)[:, None]
PU = np.zeros((nU, 3)); PU[wid] = P
E = np.unique(np.sort(np.r_[wid[F[:, [0, 1]]], wid[F[:, [1, 2]]], wid[F[:, [2, 0]]]], axis=1), axis=0)
E = E[E[:, 0] != E[:, 1]]
# islands
par = np.arange(nU)
def find(x):
    r = x
    while par[r] != r: r = par[r]
    while par[x] != r: par[x], x = r, par[x]
    return r
for a, b in E:
    ra, rb = find(a), find(b)
    if ra != rb: par[rb] = ra
root = np.array([find(i) for i in range(nU)]); isz = np.bincount(root, minlength=nU)[root]
deg = np.bincount(E.ravel(), minlength=nU).astype(float)
LO = 0.03
D0 = DU.copy()
kept = np.zeros(len(PU), bool)
for y0_, y1_, a0_, a1_, z0_, z1_ in KEEP:
    kept |= (PU[:, 1] >= y0_) & (PU[:, 1] <= y1_) & (np.abs(PU[:, 0]) >= a0_) & (np.abs(PU[:, 0]) <= a1_) & (PU[:, 2] >= z0_) & (PU[:, 2] <= z1_)
print('KEEP verts', int(kept.sum()))
for z in zones:
    f = z.split(':'); zn, js, y0, y1, n = f[0], f[1].split('|'), float(f[2]), float(f[3]), int(f[4]); A = float(f[5]) if len(f) > 5 and f[5] else 0.5
    XMAX = float(f[6]) if len(f) > 6 else 9.0      # optional: only |x| <= XMAX (keeps the shoulder puff, which hangs from the upper arm, out of a clavicle zone)
    ji = [names.index(j) for j in js if j in names]
    zw = DU[:, ji].sum(1)
    act = (zw >= LO) & (PU[:, 1] >= y0) & (PU[:, 1] <= y1) & (isz >= 60) & (np.abs(PU[:, 0]) <= XMAX)
    before = DU.copy()
    for _ in range(n):
        acc_ = np.zeros_like(DU); np.add.at(acc_, E[:, 0], DU[E[:, 1]]); np.add.at(acc_, E[:, 1], DU[E[:, 0]])
        avg = acc_ / np.maximum(deg, 1)[:, None]
        new = (1 - A) * DU + A * avg
        # keep the zone's share on the zone's joints: only the split between them moves
        Zold = DU[:, ji].sum(1, keepdims=True); Znew = np.maximum(new[:, ji].sum(1, keepdims=True), 1e-9)
        cand = DU.copy(); cand[:, ji] = new[:, ji] / Znew * Zold
        DU[act] = cand[act]
    ch = np.abs(DU - before).sum(1)
    print('ZONE', zn, 'verts', int(act.sum()), 'mean change', round(float(ch[act].mean()) if act.any() else 0, 3), 'max', round(float(ch.max()), 3))
# kept boxes get their own weights back, faded over FADE metres outside the box so no step is left at its edge
if kept.any():
    from scipy.spatial import cKDTree
    FADE = 0.02
    dd, _ = cKDTree(PU[kept]).query(PU, distance_upper_bound=FADE)
    kk = np.where(np.isfinite(dd), 1 - np.minimum(dd, FADE) / FADE, 0.0); kk = kk * kk * (3 - 2 * kk)
    DU = DU * (1 - kk[:, None]) + D0 * kk[:, None]
    print('KEEP restored', int((kk > 0).sum()), 'verts (incl. fade)')
# top 4, back to the primitives
D2 = DU[wid]
top = np.argsort(-D2, axis=1)[:, :4]; tw = np.take_along_axis(D2, top, 1); tw /= np.maximum(tw.sum(1, keepdims=True), 1e-9)
o = 0
for p in prims:
    n = g.accessors[p.attributes.POSITION].count
    J = top[o:o + n].astype('u1'); W = tw[o:o + n].astype('f4'); W[W < 1e-6] = 0
    J = np.where(W > 0, J, 0).astype('u1')
    p.attributes.JOINTS_0 = put(np.ascontiguousarray(J), 5121, 'VEC4'); p.attributes.WEIGHTS_0 = put(np.ascontiguousarray(W), 5126, 'VEC4')
    o += n
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(dst)
print('WEIGHTS written', dst)
