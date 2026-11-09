#!/usr/bin/env python3
"""Keys of the robe lattice: each point is carried by MM9's legs and tail with weights by height and azimuth (more than a vertex's 4 influences), then clamped above the floor; its frame is fitted to its ring and
column neighbours, so the cloth bends without shearing. Runs on any stage GLB with the clips; replaces earlier XRobe keys. Args: <in glb> <out glb>"""
import sys, json
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model, matrix_quaternion
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
from rig_bones import ROBE_ROWS, ROBE_COLS, robe_bone
IN, OUT = sys.argv[1:3]
FLOOR = 0.006
SETTLE = np.array([0.10, 0.40, 0.55, 0.65])      # per row, belt side to hem
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in m.joints]; ibm = {n: m.inverse_binds[i] for i, n in enumerate(jn)}
LAT = json.load(open(HERE / 'work/lattice.json'))
g_ = lambda p: np.array([p[0], p[2], -p[1]], float)
NC, NR = ROBE_COLS, len(ROBE_ROWS)
P0 = np.array([[g_(LAT[robe_bone(c, r)]) for r in range(NR)] for c in range(NC)])      # (c, r, 3)
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
TOP = 1.17
KN = np.array([0, .25, .5, .75, 1.0])                                          # height fraction: 0 belt, 1 hem
CH = dict(Pelvis=(1, .62, .22, .04, 0), Thigh=(0, .38, .56, .26, 0), Calf=(0, 0, .22, .55, .30), Foot=(0, 0, 0, .15, .70))
TL = dict(Pelvis=(1, .62, .22, .04, 0), Tail=(0, .38, .70, .46, .10), Tail1=(0, 0, .08, .50, .90))
def node_weights(c, r):
    th = 2 * np.pi * c / NC; th = (th + np.pi) % (2 * np.pi) - np.pi                 # front 0, figure's left +
    h = np.clip((TOP - ROBE_ROWS[r]) / TOP, 0, 1)
    aT = float(ss(abs(th), np.radians(95), np.radians(165)))
    aL = (1 - aT) * float(ss(th, -np.radians(60), np.radians(60))); aR = 1 - aT - aL
    w = {}
    for k, v in CH.items():
        u = float(np.interp(h, KN, v))
        if k == 'Pelvis': w['Bip01 Pelvis'] = w.get('Bip01 Pelvis', 0) + u * (aL + aR)
        else:
            w[f'Bip01 L {k}'] = u * aL; w[f'Bip01 R {k}'] = u * aR
    for k, v in TL.items():
        u = float(np.interp(h, KN, v))
        n = 'Bip01 ' + k
        w[n] = w.get(n, 0) + u * aT
    return {k: v for k, v in w.items() if v > 1e-4}
NW = [[node_weights(c, r) for r in range(NR)] for c in range(NC)]
drivers = sorted({k for row in NW for d in row for k in d})
Wm = np.zeros((NC, NR, len(drivers)))
for c in range(NC):
    for r in range(NR):
        for k, v in NW[c][r].items(): Wm[c, r, drivers.index(k)] = v
Wm /= Wm.sum(2, keepdims=True)
def kabsch(A, B):
    H = A.T @ B; U, _, Vt = np.linalg.svd(H); d = np.sign(np.linalg.det(Vt.T @ U.T)); return Vt.T @ np.diag([1, 1, d]) @ U.T
def pose(Ws):
    """lattice positions from one world pose"""
    Sk = np.array([Ws[ix[d]] @ ibm[d] for d in drivers])
    h = np.c_[P0, np.ones(P0.shape[:2] + (1,))]
    q = np.einsum('dij,crj->crdi', Sk, h)[..., :3]
    P = (q * Wm[..., None]).sum(2)
    # the displacement field is smoothed along columns and rings, so a thigh lifts the cloth instead of creasing one row
    Dsp = P - P0
    for _ in range(3):
        Dn = Dsp.copy()
        Dn[:, 1:-1] = 0.5 * Dsp[:, 1:-1] + 0.25 * (Dsp[:, :-2] + Dsp[:, 2:])
        Dn = 0.6 * Dn + 0.2 * (np.roll(Dn, 1, axis=0) + np.roll(Dn, -1, axis=0))
        Dn[:, 0] = Dsp[:, 0]; Dsp = Dn
    P = P0 + Dsp
    # a body on the floor: the robe's bell settles, the hem side most (MM9's stays a stiff cone in the air)
    sp = Ws[ix['Bip01 Neck']][:3, 3] - Ws[ix['Bip01 Pelvis']][:3, 3]; c_ = sp[1] / np.linalg.norm(sp); lying = 1 - float(ss(c_, 0.25, 0.75))
    if lying > 0:
        P[..., 1] = FLOOR + (P[..., 1] - FLOOR) * (1 - lying * SETTLE[None, :])
    # a column keeps at least 60 % of its rest spacing, from the hem up; the floor is hard
    P[..., 1] = np.maximum(P[..., 1], FLOOR)
    gap = np.linalg.norm(P0[:, :-1] - P0[:, 1:], axis=2)
    for r in range(NR - 2, 0, -1):
        d = P[:, r] - P[:, r + 1]; l = np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6); want = 0.6 * gap[:, r:r + 1]
        P[:, r] = np.where(l < want, P[:, r + 1] + d / l * want, P[:, r])
    P[..., 1] = np.maximum(P[..., 1], FLOOR)
    return P
def frames(P):
    Rs = np.zeros((NC, NR, 3, 3))
    for c in range(NC):
        for r in range(NR):
            nb = [((c + 1) % NC, r), ((c - 1) % NC, r)] + ([(c, r - 1)] if r else []) + ([(c, r + 1)] if r < NR - 1 else [])
            A = np.array([P0[a, b] - P0[c, r] for a, b in nb]); B = np.array([P[a, b] - P[c, r] for a, b in nb])
            Rs[c, r] = kabsch(A, B)
    return Rs
def level_hem(Rs, lying):
    """The hem's frames stay level on the floor, or its pleats dip through it between the lattice columns."""
    up = np.array([0, 1.0, 0]); k = 1 - lying
    for c in range(NC):
        for r, f in ((NR - 1, 1.0), (NR - 2, 0.5)):
            u_ = Rs[c, r] @ up; v = np.cross(u_, up); s_ = np.linalg.norm(v); co_ = u_ @ up
            if s_ < 1e-8: continue
            a = np.arctan2(s_, co_) * f * k; v = v / s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
            Rs[c, r] = (np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K) @ Rs[c, r]
    return Rs
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def add(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g.accessors) - 1
rn = {robe_bone(c, r) for c in range(NC) for r in range(NR)}
for an in g.animations:
    ch0 = next(c for c in an.channels if names[c.target.node] == 'Bip01 Pelvis')
    tin = an.samplers[ch0.sampler].input
    a = g.accessors[tin]; bv = g.bufferViews[a.bufferView]
    ts = np.frombuffer(bytes(blob[(bv.byteOffset or 0) + (a.byteOffset or 0):(bv.byteOffset or 0) + (a.byteOffset or 0) + 4 * a.count]), 'f4').copy()
    n = len(ts)
    T = np.zeros((n, NC, NR, 3)); Q = np.zeros((n, NC, NR, 4))
    for k, t in enumerate(ts):
        Ws = m.world(m.sample(an.name, float(t)))
        P = pose(Ws); Rs = frames(P); Wr = Ws[ix['Bip01']]; Wri = np.linalg.inv(Wr)
        sp_ = Ws[ix['Bip01 Neck']][:3, 3] - Ws[ix['Bip01 Pelvis']][:3, 3]; Rs = level_hem(Rs, 1 - float(ss(sp_[1] / np.linalg.norm(sp_), 0.25, 0.75)))
        for c in range(NC):
            for r in range(NR):
                M = np.eye(4); M[:3, :3] = Rs[c, r]; M[:3, 3] = P[c, r]
                L = Wri @ M
                T[k, c, r] = L[:3, 3]; Q[k, c, r] = matrix_quaternion(L[:3, :3])
    an.channels = [c for c in an.channels if names[c.target.node] not in rn]
    for c in range(NC):
        for r in range(NR):
            q = Q[:, c, r]
            for k in range(1, n):
                if q[k] @ q[k - 1] < 0: q[k] *= -1
            nm = ix[robe_bone(c, r)]
            s1 = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(T[:, c, r], 'VEC3'), interpolation='LINEAR'))
            s2 = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(q, 'VEC4'), interpolation='LINEAR'))
            an.channels.append(AnimationChannel(sampler=s1, target=AnimationChannelTarget(node=nm, path='translation')))
            an.channels.append(AnimationChannel(sampler=s2, target=AnimationChannelTarget(node=nm, path='rotation')))
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('ROBE keys', NC * NR, 'bones', len(g.animations), 'clips')
