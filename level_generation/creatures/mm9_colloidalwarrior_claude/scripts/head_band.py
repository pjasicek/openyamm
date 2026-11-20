#!/usr/bin/env python3
"""Head band on the exported body GLB (colloidal warrior; GLB I/O from mm9_bigfoot_claude/neck_shoulder_weights.py).
MM9 turns this neckless head 30 deg in its idle and up to 69 deg in fidgets and hits, all on Bip01 Head (mostly a twist about the spine). Measured with collapse_gate.py: a narrow band (|x| 0.18-0.30) doubled the head folds (Fidget 109 -> 209); a tall, wide one (hh -0.35..0.08, |x| 0.40-0.70) spreads the twist (Fidget 15, Hit2 61) but webbed the hood to a raised arm (AttackRanged); kept |x| 0.30-0.48 (Fidget 102, no web). The rig.s band reached
the shoulders (|x| to 0.42) and dragged the shoulder-top skin into streaks. Here every vertex's Head/Head_h weight is replaced:
band weight wh from the plane through the chin and the nape (hh = (p - C).N, full above HB1, none below HB0), narrowed across x
(full inside XA, none beyond XB); the rest of the vertex's weights carry 1 - wh; the mix goes through Head_h (helper rule);
then the band is Laplacian-smoothed ITER passes over the welded surface. Positions are glTF (y up, front +z, floor y = 0).
Args: <in glb> <out glb>"""
import os, sys
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView
from scipy.spatial import cKDTree
IN, OUT = sys.argv[1:3]
B = 'Bip01 '
RULES = (
    ('Head', 'Head_h', tuple(os.environ.get('HEAD_PARENTS', 'Spine2,Spine3,L Clavicle,R Clavicle,L UpperArm_h,R UpperArm_h').split(','))),
    ('L UpperArm', 'L UpperArm_h', ('Spine1', 'Spine2', 'Spine3', 'L Clavicle')),
    ('R UpperArm', 'R UpperArm_h', ('Spine1', 'Spine2', 'Spine3', 'R Clavicle')),
)
import os
RINGS, ITER = int(os.environ.get('RINGS', 2)), int(os.environ.get('ITER', 4))
MODE = os.environ.get('MODE', 'helper')          # helper: through the half helper, then smooth; smooth: smoothing only
ONLY = os.environ.get('ONLY', '')                  # e.g. 'Head' or 'L UpperArm,R UpperArm'
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
names = [g.nodes[j].name for j in g.skins[0].joints]; ix = {n: i for i, n in enumerate(names)}


def acc(i, dt):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)


prims = [p for m in g.meshes for p in m.primitives]
P = np.vstack([acc(p.attributes.POSITION, 'f4') for p in prims]).astype(float)
J = np.vstack([acc(p.attributes.JOINTS_0, 'u1') for p in prims]).astype(int)
W = np.vstack([acc(p.attributes.WEIGHTS_0, 'f4') for p in prims]).astype(float)
T = np.vstack([acc(p.indices, {5123: 'u2', 5125: 'u4'}[g.accessors[p.indices].componentType]).reshape(-1, 3).astype(int) + o
               for p, o in zip(prims, np.cumsum([0] + [g.accessors[p.attributes.POSITION].count for p in prims])[:-1])])
n = len(P)
D = np.zeros((n, len(names)))
np.add.at(D, (np.repeat(np.arange(n), 4), J.ravel()), W.ravel())
# weld by position: seam duplicates share their weights and their neighbours
_, uid = np.unique(np.round(P, 5), axis=0, return_inverse=True); uid = uid.ravel()
nu = uid.max() + 1
E = np.unique(np.sort(np.r_[uid[T[:, [0, 1]]], uid[T[:, [1, 2]]], uid[T[:, [2, 0]]]], axis=1), axis=0)
nbr = [[] for _ in range(nu)]
for a, b in E:
    if a != b: nbr[a].append(b); nbr[b].append(a)
Du = np.zeros((nu, len(names))); cnt = np.zeros(nu)
np.add.at(Du, uid, D); np.add.at(cnt, uid, 1); Du /= cnt[:, None]
report = []
sm = lambda a, b, v: (lambda u: u * u * (3 - 2 * u))(np.clip((v - a) / (b - a), 0, 1))
LIFT = float(os.environ.get('LIFT', 1.0134))
HB0, HB1 = float(os.environ.get('HB0', -0.35)), float(os.environ.get('HB1', 0.08))
XA, XB = float(os.environ.get('XA', 0.30)), float(os.environ.get('XB', 0.48))
ITER = int(os.environ.get('ITER', 6))
Pu = np.zeros((nu, 3)); np.add.at(Pu, uid, P); Pu /= cnt[:, None]
Bx, By, Bz = Pu[:, 0], -Pu[:, 2], Pu[:, 1] - LIFT          # Blender rest frame of the fit scripts
C = np.array([0.0, -0.35, 0.53]); Nk = np.array([0.0, -0.43, 1.0]); Nk /= np.linalg.norm(Nk)
hh = (np.c_[Bx, By, Bz] - C) @ Nk
wh = sm(HB0, HB1, hh) * (1 - sm(XA, XB, np.abs(Bx)))
hd, hh_ = ix[B + 'Head'], ix[B + 'Head_h']
old = Du[:, hd] + Du[:, hh_]
Du[:, hd] = 0; Du[:, hh_] = 0
rest = Du.sum(1)
nk = ix[B + 'Neck']
Du[rest < 1e-6, nk] = 1.0; rest = Du.sum(1)
Du = Du / rest[:, None]
t = wh
Du *= np.maximum(1 - 2 * t, 0)[:, None]
Du[:, hh_] = 1 - np.abs(2 * t - 1)
Du[:, hd] = np.maximum(2 * t - 1, 0)
band = (wh > 1e-3) & (wh < 0.999)
for _ in range(2):
    grow = band.copy()
    for v in np.where(band)[0]: grow[nbr[v]] = True
    band = grow
for _ in range(ITER):
    new = Du.copy()
    for v in np.where(band)[0]:
        if nbr[v]: new[v] = 0.5 * Du[v] + 0.5 * Du[nbr[v]].mean(0)
    Du = new
report.append(f'head band: {int((wh > 0.5).sum())} on the head, band {int(band.sum())}, was {int((old > 0.5).sum())} > 0.5')
# 4 largest per vertex, normalised, back to the duplicates
order = np.argsort(-Du, axis=1)[:, :4]
Wn = np.take_along_axis(Du, order, 1); Wn[Wn < 0.01] = 0; Wn /= np.maximum(Wn.sum(1, keepdims=True), 1e-9)
Jn = np.where(Wn > 0, order, 0)
Jv, Wv = Jn[uid], Wn[uid]
off = 0
def put(arr, ctype, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=ctype, count=len(arr), type=typ))
    return len(g.accessors) - 1
for p in prims:
    k = g.accessors[p.attributes.POSITION].count
    p.attributes.JOINTS_0 = put(Jv[off:off + k].astype('u1'), 5121, 'VEC4')
    p.attributes.WEIGHTS_0 = put(Wv[off:off + k].astype('f4'), 5126, 'VEC4')
    off += k
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('WEIGHTS', '; '.join(report))
