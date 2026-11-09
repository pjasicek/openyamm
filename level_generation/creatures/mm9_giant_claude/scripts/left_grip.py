#!/usr/bin/env python3
"""Left fingers round the shaft (after grip_lock.py). MM9's left mitten lies on the shaft in Standing, Walking, Running and part of
the attacks without closing on it; its curl (finger_keys_giant.py) put our fingers 2.6 cm into the shaft. Per key of the left finger
channels: the shaft line is taken into the hand's rest frame, and each finger takes the curl about its knuckle line closest to the
key's own curl that keeps every sample from the middle phalanx on at least the shaft radius + half the finger + 4 mm from the shaft's
axis (inside a slab along the shaft), the base segment being fixed. Keys are solved in order with a continuity term (averaging two clear solutions can pass through the shaft), then lightly low-passed, then written as
bone-local rotations the way finger_keys_giant.py writes them. Args: <in glb> <out glb>"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
from pygltflib import GLTF2
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
IN, OUT = sys.argv[1:3]
R_SHAFT = 0.030
import os
PAD = float(os.environ.get('LG_PAD', 1.6)); CONT = float(os.environ.get('LG_CONT', 0.5))
P = json.load(open(HERE / 'work' / 'hand_poses.json')); FL = P['flexL']; AXL = np.array(FL['AX']); SG = FL['sg']; RB = {k: np.array(v) for k, v in FL['Rb'].items()}
GJ = json.load(open(HERE / 'work' / 'hands_v1.json'))['joints']['L']
FN = {'Index': 2, 'Middle': 3, 'Ring': 4, 'Pinky': 5}
JL = {f: np.array([GJ[f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[f'finger{k}-3_tip']]) for f, k in FN.items()}
HALF = {'Index': 0.0187, 'Middle': 0.0175, 'Ring': 0.0169, 'Pinky': 0.0133}
m = Model(Glb(IN)); d = m.glb.json; names = [n.get('name') for n in d['nodes']]
iH, iX = names.index('Bip01 L Hand'), names.index('Xhammer')
B2G = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1.0]])     # Blender world -> glTF world (rest rig has no lift in hands_v1 joints)
Hrest = m.world({})[iH]
lift = np.array(d['nodes'][names.index('MM9_Rig')].get('translation', [0, 0, 0]))          # the armature object carries the floor lift
def rodr(ax, ang):
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); c, s = np.cos(ang)[:, None, None], np.sin(ang)[:, None, None]
    return np.eye(3)[None] + s * K[None] + (1 - c) * (K @ K)[None]
A1, A2, A3 = np.meshgrid(np.radians(np.arange(-36, 101, 4)),       # back to -36 deg: the finger may open off a shaft through its root
                          np.radians(np.arange(0, 116, 5)), np.radians(np.arange(0, 91, 5)), indexing='ij')
A1, A2, A3 = A1.ravel(), A2.ravel(), A3.ravel()
# FK samples per finger in Blender rest world, then to glTF rest world
FK = {}
for f, j in JL.items():
    R1, R2, R3 = rodr(AXL, SG * A1), rodr(AXL, SG * (A1 + A2)), rodr(AXL, SG * (A1 + A2 + A3))
    p1 = j[0] + R1 @ (j[1] - j[0]); p2 = p1 + R2 @ (j[2] - j[1]); p3 = p2 + R3 @ (j[3] - j[2])
    j0 = np.broadcast_to(j[0], p1.shape)
    S_ = np.stack([a + (b - a) * t for a, b, ts_ in ((j0, p1, (0.5, 0.75)), (p1, p2, (0.0, 0.25, 0.5, 0.75, 1.0)), (p2, p3, (0.25, 0.5, 0.75, 1.0))) for t in ts_], 1)      # the proximal phalanx too (fingers 1 ran through the shaft)
    FK[f] = (np.c_[S_.reshape(-1, 3), np.ones(S_.size // 3)] @ B2G.T)[:, :3].reshape(S_.shape) + lift
TJ = np.array([GJ[f'finger1-{j}'] for j in (1, 2, 3)] + [GJ['finger1-3_tip']])
f0L = np.mean([JL[f][1] - JL[f][0] for f in FN], 0); f0L -= AXL * (f0L @ AXL); f0L /= np.linalg.norm(f0L)
TH, PH = np.meshgrid(np.radians(np.arange(-90, 91, 6)), np.radians(np.arange(-90, 91, 6)), indexing='ij'); TH, PH = TH.ravel(), PH.ravel()
RT = rodr(AXL, PH) @ rodr(f0L, TH)
TS = np.stack([TJ[0] + (RT @ (TJ[k] - TJ[0]))[:, :] for k in (1, 2, 3)], 1)
TS = np.concatenate([TS, (TS[:, :2] + TS[:, 1:]) / 2], 1)
TS = (np.c_[TS.reshape(-1, 3), np.ones(TS.size // 3)] @ B2G.T)[:, :3].reshape(TS.shape) + lift

# ---- the path over keys (2026-10-31, second pass): each finger and the thumb take one pose per key from a grid, chosen for the whole
# clip at once (Viterbi): off the shaft at the keys AND at the midpoints between keys (the keys interpolate: two clear poses on either
# side of the shaft made the per-key solve pass the finger through it), near MM9's curl where that is clear, without jumps
G1, G2 = np.radians(np.arange(-36, 101, 4)), np.radians(np.arange(0, 116, 5))
GA = np.stack(np.meshgrid(G1, G2, indexing='ij'), -1).reshape(-1, 2)           # (MCP, PIP); DIP = 0.75 PIP
H1, H2 = np.radians(np.arange(-36, 101, 2)), np.radians(np.arange(0, 116, 2.5))
GH = np.stack(np.meshgrid(H1, H2, indexing='ij'), -1).reshape(-1, 2)
gi = np.stack(np.meshgrid(np.arange(len(G1)), np.arange(len(G2)), indexing='ij'), -1).reshape(-1, 2)
HIDX = (gi[:, None, 0] + gi[None, :, 0]) * len(H2) + (gi[:, None, 1] + gi[None, :, 1])
D2G = ((GA[:, None] - GA[None]) ** 2).sum(-1)
def fk_fingers(j, A):
    a1, a2 = A[:, 0], A[:, 1]; a3 = 0.75 * a2
    R1, R2, R3 = rodr(AXL, SG * a1), rodr(AXL, SG * (a1 + a2)), rodr(AXL, SG * (a1 + a2 + a3))
    p1 = j[0] + R1 @ (j[1] - j[0]); p2 = p1 + R2 @ (j[2] - j[1]); p3 = p2 + R3 @ (j[3] - j[2])
    j0 = np.broadcast_to(j[0], p1.shape)
    S_ = np.stack([a + (b - a) * t for a, b, ts_ in ((j0, p1, (0.5, 0.75)), (p1, p2, (0.0, 0.25, 0.5, 0.75, 1.0)), (p2, p3, (0.25, 0.5, 0.75, 1.0))) for t in ts_], 1)
    return (np.c_[S_.reshape(-1, 3), np.ones(S_.size // 3)] @ B2G.T)[:, :3].reshape(S_.shape) + lift
FKg = {f: fk_fingers(j, GA) for f, j in JL.items()}; FKh = {f: fk_fingers(j, GH) for f, j in JL.items()}
T1 = np.radians(np.arange(-90, 91, 6)); T2 = np.radians(np.arange(-90, 91, 3))
TA = np.stack(np.meshgrid(T1, T1, indexing='ij'), -1).reshape(-1, 2); TAh = np.stack(np.meshgrid(T2, T2, indexing='ij'), -1).reshape(-1, 2)
ti = np.stack(np.meshgrid(np.arange(len(T1)), np.arange(len(T1)), indexing='ij'), -1).reshape(-1, 2)
THIDX = (ti[:, None, 0] + ti[None, :, 0]) * len(T2) + (ti[:, None, 1] + ti[None, :, 1])
D2T = ((TA[:, None] - TA[None]) ** 2).sum(-1)
def fk_thumb(A):
    R_ = rodr(AXL, A[:, 1]) @ rodr(f0L, A[:, 0])
    X = np.stack([TJ[0] + (R_ @ (TJ[k] - TJ[0])) for k in (1, 2, 3)], 1); X = np.concatenate([X, (X[:, :2] + X[:, 1:]) / 2], 1)
    return (np.c_[X.reshape(-1, 3), np.ones(X.size // 3)] @ B2G.T)[:, :3].reshape(X.shape) + lift
TSg, TSh = fk_thumb(TA), fk_thumb(TAh)
def pen_of(X, o, a, want):
    v = X - o; al = v @ a; r = np.linalg.norm(v - al[..., None] * a, axis=-1); slab = (al > -0.40) & (al < 1.30)
    return ((np.maximum(want - r, 0) * slab) ** 2).sum(1)
def viterbi(pk, dev, pm, hidx, d2):
    """pk (K, S) penetration per key and state, dev (K, S) squared distance from MM9's pose, pm K-1 arrays over the half grid"""
    K, S = pk.shape
    clear = pk[np.arange(K), dev.argmin(1)] == 0                 # MM9's own pose is clear: follow it closely
    cost = 2000 * pk + np.where(clear[:, None], 1.0, 0.01) * dev
    acc_ = cost[0].copy(); back = np.zeros((K, S), int)
    for k in range(1, K):
        tr = acc_[:, None] + 2000 * pm[k - 1][hidx] + 0.02 * d2
        back[k] = tr.argmin(0); acc_ = tr[back[k], np.arange(S)] + cost[k]
    path = np.zeros(K, int); path[-1] = int(acc_.argmin())
    for k in range(K - 1, 0, -1): path[k - 1] = back[k, path[k]]
    return path
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()
def put(i, arr):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    blob[off:off + arr.size * 4] = arr.astype('f4').tobytes()
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
def rot(ax, a):
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
def m2q(R):
    t = np.trace(R)
    if t > 0:
        s = np.sqrt(t + 1) * 2; return np.array([(R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, s / 4])
    i = int(np.argmax(np.diag(R))); j, k = (i + 1) % 3, (i + 2) % 3
    s = np.sqrt(1 + R[i, i] - R[j, j] - R[k, k]) * 2; q = np.zeros(4)
    q[i] = s / 4; q[j] = (R[j, i] + R[i, j]) / s; q[k] = (R[k, i] + R[i, k]) / s; q[3] = (R[k, j] - R[j, k]) / s
    return q
idx = {n.name: i for i, n in enumerate(g.nodes)}
def rest_q(n): return np.array(g.nodes[idx[n]].rotation or [0, 0, 0, 1], float)
def ang_from_rest(vals, n):
    ri = rest_q(n) * np.array([-1, -1, -1, 1]); dd = np.array([qmul(ri, v) for v in vals]); return 2 * np.arccos(np.clip(np.abs(dd[:, 3]), -1, 1))
KF = {'Index': (0.9, 0.85, 0.7), 'Middle': (1.0, 0.9, 0.75), 'Ring': (1.0, 0.95, 0.8), 'Pinky': (1.05, 1.0, 0.85)}
IKW = json.load(open(HERE / 'work' / 'left_ik.json')) if (HERE / 'work' / 'left_ik.json').exists() else {}
def keep_ik(name, tt, vals, cur):
    # where left_ik.py closed the fist on the shaft (weight w), its keys stay: this pass only acts outside the grip
    if name not in IKW: return vals
    wk = np.interp(tt, IKW[name]['times'], IKW[name].get('wf', IKW[name]['w']))       # the fist's closing weight: outside it this pass clears the fingers
    return np.array([slerp_q(vals[k], cur[k], wk[k]) for k in range(len(vals))])
def slerp_q(a, b, t):
    if a @ b < 0: b = -b
    q = a * (1 - t) + b * t; return q / np.linalg.norm(q)
rep = {}
ONLY = [c for c in os.environ.get('LG_CLIPS', '').split(',') if c]        # r23: a second pass on the clips the post-grip bumps moved
for an in g.animations:
    if ONLY and an.name not in ONLY: continue
    ch = {(g.nodes[c.target.node].name, c.target.path): c for c in an.channels}
    sm0 = an.samplers[ch[('Bip01 L Finger1', 'rotation')].sampler]; ts = acc(sm0.input)[:, 0]
    th = [ang_from_rest(acc(an.samplers[ch[(f'Bip01 L {k}', 'rotation')].sampler].output), f'Bip01 L {k}') for k in ('Finger1', 'Finger11', 'Finger12')]
    th = [np.interp(ts, acc(an.samplers[ch[(f'Bip01 L {k}', 'rotation')].sampler].input)[:, 0], v) for k, v in zip(('Finger1', 'Finger11', 'Finger12'), th)]
    # the shaft line per key in the hand's rest frame, and its midpoint between keys (where the keys interpolate)
    OA = []
    for i, t in enumerate(ts):
        w = m.world(m.sample(an.name, float(t))); T = Hrest @ np.linalg.inv(w[iH])           # posed world -> rest world, through the hand
        o = (T @ np.r_[w[iX][:3, 3], 1])[:3]; a = T[:3, :3] @ (w[iX][:3, 1] / np.linalg.norm(w[iX][:3, 1])); OA.append((o, a / np.linalg.norm(a)))
    MID = [((o0 + o1) / 2, (a0 + a1) / np.linalg.norm(a0 + a1)) for (o0, a0), (o1, a1) in zip(OA[:-1], OA[1:])]
    sol = {f: np.zeros((len(ts), 3)) for f in FN}; moved = 0.0; tsol = np.zeros((len(ts), 2))
    for f in FN:
        k1, k2, k3 = KF[f]; want = R_SHAFT + PAD * HALF[f] + 0.012
        tg = np.stack([k1 * th[0], k2 * th[1]], 1)
        dev = ((GA[None, :, :] - tg[:, None, :]) ** 2).sum(-1)
        pk = np.array([pen_of(FKg[f], o, a, want) for o, a in OA]); pm = [pen_of(FKh[f], o, a, want) for o, a in MID]
        path = viterbi(pk, dev, pm, HIDX, D2G)
        sol[f] = np.c_[GA[path], 0.75 * GA[path, 1]]
        exact = np.stack([k1 * th[0], k2 * th[1], k3 * th[2]], 1)          # where MM9's own curl is clear and the path sits on it, its exact angles
        ok_ = (pk[np.arange(len(ts)), dev.argmin(1)] == 0) & (path == dev.argmin(1))
        sol[f][ok_] = exact[ok_]
        moved = max(moved, float(np.degrees(np.sqrt(dev[np.arange(len(ts)), path].max()))))
    pk = np.array([pen_of(TSg, o, a, R_SHAFT + PAD * 0.0186 + 0.012) for o, a in OA]); pm = [pen_of(TSh, o, a, R_SHAFT + PAD * 0.0186 + 0.012) for o, a in MID]
    devt = np.broadcast_to((TA ** 2).sum(1), pk.shape)
    path = viterbi(pk, devt, pm, THIDX, D2T); tsol = TA[path]
    c_ = ch.get(('Bip01 L Thumb1', 'rotation'))
    if c_ is not None:
        sm = an.samplers[c_.sampler]; tt = acc(sm.input)[:, 0]; out = []
        for q in range(len(tt)):
            th_, ph_ = np.interp(tt[q], ts, tsol[:, 0]), np.interp(tt[q], ts, tsol[:, 1])
            D = rot(AXL, ph_) @ rot(f0L, th_); Rb = RB['Bip01 L Thumb1']; out.append(qmul(rest_q('Bip01 L Thumb1'), m2q(Rb.T @ D @ Rb)))
        put(sm.output, keep_ik(an.name, tt, np.array(out), acc(sm.output)))
    rep[an.name + '_thumb'] = round(float(np.degrees(np.abs(tsol).max())), 1)
    rep[an.name] = round(moved, 1)
    for f in FN:
        for seg in range(3):
            n = f'Bip01 L {f}{seg + 1}'; c_ = ch.get((n, 'rotation'))
            if c_ is None: continue
            sm = an.samplers[c_.sampler]; tt = acc(sm.input)[:, 0]
            S_ = np.stack([np.interp(tt, ts, sol[f][:, k]) for k in range(3)], 1); cum = np.cumsum(S_, 1)
            out = []
            for q in range(len(tt)):
                D = rot(AXL, SG * cum[q, seg]); prev = rot(AXL, SG * cum[q, seg - 1]) if seg > 0 else np.eye(3)
                Rb = RB[n]; out.append(qmul(rest_q(n), m2q(Rb.T @ prev.T @ D @ Rb)))
            put(sm.output, keep_ik(an.name, tt, np.array(out), acc(sm.output)))
g.set_binary_blob(bytes(blob)); g.save(OUT)
print('LEFTGRIP largest change from the clip curl, deg', rep)
