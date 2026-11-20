#!/usr/bin/env python3
"""Neck and armpit weights for the collapse gate (run 2 follow-up, 2026-10-31). On a GLB of the body, before clips; meshes,
UVs, joints and clips are kept, only JOINTS_0/WEIGHTS_0 are rewritten.

Found: the gorilla's head joint sits 5 cm above the clavicles, and helpers_bf.py only split Head against Spine3 and UpperArm
against Clavicle/Spine3. So the neck side and the jaw rim mixed Head straight with the clavicles and UpperArm_h (MM9's
100-118 deg head turns fold them: head 44 in WalkFidget), and the armpit mixed UpperArm straight with Spine1/Spine2 (arms
overhead fold it: shoulder 24 in AttackMelee).
Per rule (child, helper, parents): where a vertex mixes the child with any parent, the mix goes through the half-rotation
helper as helpers_bf.py does (t = child share: child (2t-1)+, helper 1-|2t-1|, parents (1-2t)+), then the band (those
vertices and RINGS rings round them) is Laplacian-smoothed over the welded surface, ITER passes, and every vertex keeps its
4 largest weights. (colloidal warrior copy: FLANK_SPLIT / FLANK_BONES choose the spine bones the flank goes to.) Args: <in glb> <out glb>"""
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
THROAT = os.environ.get('THROAT', '')          # e.g. '0.08,0.18': near the midline the neck's clavicle weight goes to Spine3
if THROAT:
    x0, x1 = (float(v) for v in THROAT.split(','))
    hd = ix[B + 'Head']; s3 = ix[B + 'Spine3']; cl = [ix[B + k] for k in ('L Clavicle', 'R Clavicle', 'L UpperArm_h', 'R UpperArm_h')]
    Pu = np.zeros((nu, 3)); np.add.at(Pu, uid, P); Pu /= cnt[:, None]
    u = np.clip((x1 - np.abs(Pu[:, 0])) / (x1 - x0), 0, 1); f = u * u * (3 - 2 * u)
    neck = (Du[:, hd] > 1e-3) | (Du[:, ix[B + 'Head_h']] > 1e-3)
    moved = (Du[:, cl] * (f * neck)[:, None]).sum(1)
    Du[:, cl] *= (1 - f * neck)[:, None]; Du[:, s3] += moved
    report.append(f'throat: {int((moved > 1e-3).sum())} vertices to Spine3')
FLANK = os.environ.get('FLANK', '')            # 'x1,ytop': the torso's side wall under the armpit carried UpperArm weight
if FLANK:
    fx1, ytop, XR, YR, ZF = (float(v) for v in (FLANK + ',0.08,0.2,9').split(',')[:5])
    Pu = np.zeros((nu, 3)); np.add.at(Pu, uid, P); Pu /= cnt[:, None]
    Nv = np.vstack([acc(p.attributes.NORMAL, 'f4') for p in prims]).astype(float)
    Nu = np.zeros((nu, 3)); np.add.at(Nu, uid, Nv); Nu /= np.maximum(np.linalg.norm(Nu, axis=1, keepdims=True), 1e-9)
    sm = lambda a, b, v: (lambda u: u * u * (3 - 2 * u))(np.clip((v - a) / (b - a), 0, 1))
    for sd, sg in (('L', 1), ('R', -1)):
        ua, uh = ix[f'{B}{sd} UpperArm'], ix[f'{B}{sd} UpperArm_h']; s1, s2 = (ix[B + k] for k in os.environ.get('FLANK_BONES', 'Spine1,Spine2').split(','))
        x = Pu[:, 0] * sg; y = Pu[:, 1]
        wall = (x > 0.12) & (x < fx1) & (Nu[:, 0] * sg > 0.2) & (y < ytop) & (Du[:, ua] + Du[:, uh] > 1e-3)
        out = sm(ytop, ytop - YR, y) * sm(fx1, fx1 - XR, x) * sm(ZF + 0.08, ZF, Pu[:, 2])      # low on the wall, fading out at the armpit, the arm and the front fold
        k = np.where(wall, out, 0.0)
        mv = (Du[:, ua] + Du[:, uh]) * k
        Du[:, ua] *= 1 - k; Du[:, uh] *= 1 - k
        lo_hi = [float(v) for v in os.environ.get('FLANK_SPLIT', '1.65,1.85').split(',')]      # colloidal: 1.25,1.45 and FLANK_BONES=Spine2,Spine3
        up = sm(lo_hi[0], lo_hi[1], y)                                          # lower spine bone low, upper high
        Du[:, s1] += mv * (1 - up); Du[:, s2] += mv * up
        band = wall.copy()
        for v in np.where(wall)[0]: band[nbr[v]] = True
        cols = [ua, uh, s1, s2, ix[B + 'Spine3'], ix[f'{B}{sd} Clavicle']]
        for _ in range(3):
            new = Du.copy()
            for v in np.where(band)[0]:
                if nbr[v]:
                    sv = Du[v, cols].sum(); avg = Du[nbr[v]][:, cols].mean(0)
                    if avg.sum() > 1e-9: new[v, cols] = 0.5 * Du[v, cols] + 0.5 * avg / avg.sum() * sv
            Du = new
        report.append(f'flank {sd}: {int(wall.sum())} vertices, {float(mv.sum()):.1f} weight to the spine')
for child, helper, parents in RULES:
    if ONLY and child not in ONLY.split(','): continue
    c, h = ix[B + child], ix[B + helper]; ps = [ix[B + p] for p in parents]
    wc = Du[:, c]; wp = Du[:, ps].sum(1); tot = wc + wp
    mix = (wc > 1e-3) & (wp > 1e-3)
    t = np.where(mix, wc / np.maximum(tot, 1e-9), 0)
    if MODE == 'helper':
        sc = np.maximum(1 - 2 * t, 0)
        for p in ps: Du[mix, p] *= sc[mix]
        Du[mix, h] += tot[mix] * (1 - np.abs(2 * t[mix] - 1))
        Du[mix, c] = tot[mix] * np.maximum(2 * t[mix] - 1, 0)
    band = mix.copy()
    for _ in range(RINGS):
        grow = band.copy()
        for v in np.where(band)[0]: grow[nbr[v]] = True
        band = grow
    cols = [c, h] + ps
    for _ in range(ITER):
        new = Du.copy()
        for v in np.where(band)[0]:
            if nbr[v]:
                s = Du[v, cols].sum()
                avg = Du[nbr[v]][:, cols].mean(0)
                if avg.sum() > 1e-9:
                    new[v, cols] = 0.5 * Du[v, cols] + 0.5 * avg / avg.sum() * s       # the rule's joints only, their total kept
        Du = new
    report.append(f'{child}: mixed {int(mix.sum())} band {int(band.sum())}')
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
