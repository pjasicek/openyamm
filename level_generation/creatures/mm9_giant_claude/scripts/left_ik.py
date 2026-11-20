#!/usr/bin/env python3
"""Two-handed grip: wherever MM9's left mitten lies on the shaft, our left fist closes round it (coordinator, 2026-10-31: the fist
closes round the shaft, no finger through it; the left hand may slide along the shaft). After arm_fix.sh and the mallet bumps.
Per clip and key (glb_pose):
- w: how far MM9's left palm point (its bind grip point, 14.7 cm from the wrist) lies from the shaft's axis: 1 under 7 cm, 0 over 13 cm,
  low-passed over keys;
- target: the hole centre on the axis at the palm's own position along it, kept at least GAP from the right fist and on the shaft;
  the hand turned by the least rotation that lines its hole axis up with the shaft;
- two-bone IK of the upper arm and forearm to the wrist that puts the hole there (elbow kept in its own plane), the hand's rotation set;
- UpperArm, Forearm and Hand local rotations slerped from MM9's by w; the left finger and thumb bones from their keys to the fist
  (work/hand_poses.json gripL) by w.
Writes work/left_ik.json (w per clip and key, reach misses). Args: <in glb> <out glb>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion
from pygltflib import GLTF2
HERE = Path(__file__).resolve().parents[1]
IN, OUT = sys.argv[1:3]
GAP, NEAR, FAR = float(__import__('os').environ.get('IK_GAP', 0.17)), 0.10, 0.16
SOFT = float(__import__('os').environ.get('IK_SOFT', 0.03))
DIL = int(__import__('os').environ.get('IK_DIL', 3))
GAPFILL = int(__import__('os').environ.get('IK_GAPFILL', 4)); FADE = float(__import__('os').environ.get('IK_FADEKEYS', 3.0))
QSIG = float(__import__('os').environ.get('IK_QSIG', 0.0))
P = json.load(open(HERE / 'work' / 'hand_poses.json'))
m = Model(Glb(IN)); d = m.glb.json; names = [n.get('name') for n in d['nodes']]
ix = {n: i for i, n in enumerate(names)}
iU, iF, iH, iRH, iX = (ix[n] for n in ('Bip01 L UpperArm', 'Bip01 L Forearm', 'Bip01 L Hand', 'Bip01 R Hand', 'Xhammer'))
lift = np.array(d['nodes'][ix['MM9_Rig']].get('translation', [0, 0, 0]))
B2G = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.]])
Hrest = m.world({})[iH]
Gg = B2G @ np.array(P['holeL']['G_world']) + lift
Ag = B2G @ np.array(P['holeL']['axis_world'])
g_loc = (np.linalg.inv(Hrest) @ np.r_[Gg, 1])[:3]; a_loc = Hrest[:3, :3].T @ Ag; a_loc /= np.linalg.norm(a_loc)
gR_loc = (np.linalg.inv(m.world({})[iRH]) @ np.r_[B2G @ np.array(P['holeR']['G_turned_world']) + lift, 1])[:3]     # the right fist's hole (the gap is between the holes)
def minrot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = float(a @ b); s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
def ortho(R):
    u, _, vt = np.linalg.svd(R); return u @ vt
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
def slerp(a, b, t):
    if a @ b < 0: b = -b
    q = a * (1 - t) + b * t; return q / np.linalg.norm(q)
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()
def put(i, arr):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    blob[off:off + arr.size * 4] = arr.astype('f4').tobytes()
FING = [n for n in names if n and n.startswith('Bip01 L ') and any(k in n for k in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
rest_q = lambda n: np.array(d['nodes'][ix[n]].get('rotation', [0, 0, 0, 1]), float)
MM9_PALM = np.array([-0.132, 0.0, 0.065])     # MM9's own grip point in its hand frame (the right one at bind, mirrored), for the weight
import os
# Fidget left out again (r23): the r22 regrip snapped the fingers shut while the shaft passed through them (left fingers 2.9 cm in the shaft)
CLIPS = os.environ.get('IK_CLIPS', 'Standing,Walking,Running,Fidget2,Taunt,Aware,AttackMelee,AttackMelee2').split(',')      # third pass: every clip where MM9's left mitten lies on the shaft for half the clip or more (AttackMelee: its ends)
rep = {}
for an in g.animations:
    if an.name not in CLIPS: continue
    ch = {(g.nodes[c.target.node].name, c.target.path): c for c in an.channels}
    sm = an.samplers[ch[('Bip01 L UpperArm', 'rotation')].sampler]; ts = acc(sm.input)[:, 0]
    W_ = [m.world(m.sample(an.name, float(t))) for t in ts]
    w_raw = np.zeros(len(ts)); dmm = np.zeros(len(ts))
    for k, W in enumerate(W_):
        o = W[iX][:3, 3]; a = W[iX][:3, 1] / np.linalg.norm(W[iX][:3, 1]); p = (W[iH] @ np.r_[MM9_PALM, 1])[:3]
        v = p - o; dist = np.linalg.norm(v - a * (v @ a)); dmm[k] = dist
        w_raw[k] = np.clip((FAR - dist) / (FAR - NEAR), 0, 1)
    ENDS = an.name in os.environ.get('IK_ENDS', 'AttackMelee').split(',')
    w = ndimage.gaussian_filter1d(w_raw, 3.0, mode='nearest'); w = w * w * (3 - 2 * w)
    # stable per clip: the hand's axis sign and the side of the right fist the left one holds (per-key choices flipped and jittered)
    pre = []
    for k, W in enumerate(W_):
        o = W[iX][:3, 3]; a = W[iX][:3, 1] / np.linalg.norm(W[iX][:3, 1]); p = (W[iH] @ np.r_[g_loc, 1])[:3]
        pre.append(((p - o) @ a, ((W[iRH] @ np.r_[gR_loc, 1])[:3] - o) @ a, float((ortho(W[iH][:3, :3]) @ a_loc) @ a)))
    pre = np.array(pre); wsum = max(w.sum(), 1e-6)
    SIGN = 1.0 if (pre[:, 2] * w).sum() >= 0 else -1.0
    SIDE = 1.0 if ((pre[:, 0] - pre[:, 1]) * w).sum() >= 0 else -1.0
    s_t = pre[:, 0].copy()
    lo = pre[:, 1] + GAP                                                # held on SIDE of the right fist, at least GAP from it
    s_t = np.maximum(s_t, lo) if SIDE > 0 else np.minimum(s_t, pre[:, 1] - GAP)
    # reach: where the arm cannot get the fist onto the shaft at that spot, slide along it to the nearest spot it reaches (on SIDE)
    okm = np.zeros(len(ts), bool)
    for k, W in enumerate(W_):
        o = W[iX][:3, 3]; a = W[iX][:3, 1] / np.linalg.norm(W[iX][:3, 1]); S0 = W[iU][:3, 3]
        L12 = np.linalg.norm(W[iF][:3, 3] - S0) + np.linalg.norm(W[iH][:3, 3] - W[iF][:3, 3]) - SOFT
        Rc = ortho(W[iH][:3, :3]); ac = Rc @ a_loc; Rt = minrot(ac, a * SIGN) @ Rc
        cands = sorted(np.arange(-0.30, 1.221, 0.02), key=lambda x: abs(x - s_t[k]))
        ok = False
        for sc in cands:
            if SIDE * (sc - pre[k, 1]) < GAP: continue
            if np.linalg.norm((o + a * sc) - Rt @ g_loc - S0) <= L12: s_t[k] = sc; ok = True; break
        if os.environ.get('IK_DBG') == an.name: print('DBG', k, 'w_raw', round(float(w_raw[k]), 2), 'ok', ok, 'side', SIDE, 'sR', round(float(pre[k, 1]), 2), 's_palm', round(float(pre[k, 0]), 2), 'best excess cm', round(100 * min(np.linalg.norm((o + a * sc) - Rt @ g_loc - S0) - L12 for sc in cands), 1))
        okm[k] = ok                                # out of reach: the fist stays open there (left_grip.py keeps the fingers off the shaft)
    s_t = ndimage.gaussian_filter1d(np.clip(s_t, -0.30, 1.22), 2.0, mode='nearest')
    # the grip held DIL keys past where MM9's palm leaves the shaft wherever the arm reaches (the fades then fall outside MM9's own grip)
    near = w_raw > 0.5
    if os.environ.get('IK_DBG_NEAR'): print('NEAR', an.name, round(float(near.mean()), 2), 'okm', round(float(okm.mean()), 2))
    if ENDS:
        # the swing: MM9 lets go of the shaft overhead and through the blow and its brief catch at the top of the swing puts the fists in each other:
        # the grip is held only where the clip starts and ends, and fades with MM9's own hand coming back (closeness over 5-30 cm: no extra rush)
        lab, nl = ndimage.label(dmm < 0.30); keep = {lab[0], lab[-1]} - {0}
        run = np.isin(lab, list(keep)); dil = 0
        cont = np.clip((0.30 - dmm) / 0.25, 0, 1) * run; cont = cont * cont * (3 - 2 * cont)
        near = cont > 0.99
    else:
        dil = DIL
    dn = ndimage.binary_dilation(near, iterations=dil) if dil else near
    hold = okm & dn
    if not ENDS and GAPFILL: hold = ndimage.binary_closing(np.r_[hold[-1:], hold, hold[:1]], iterations=GAPFILL)[1:-1] | hold     # short drops of the grip held (each release and regrip jerked)
    w_raw = np.where(hold, 1.0, 0.0)
    if ENDS: w_raw = np.where(okm, cont, 0.0)
    w = ndimage.gaussian_filter1d(w_raw, FADE, mode='wrap' if not ENDS else 'nearest'); w = np.clip(w, 0, 1); w = w * w * (3 - 2 * w)      # loops wrap: the seam eases like any other key
    w = np.maximum(w, ndimage.binary_erosion(w_raw > 0.99, iterations=1, border_value=1))       # full grip inside the run (the clip's first key matches Standing)
    wf_ = None
    out = {n: [] for n in ('Bip01 L UpperArm', 'Bip01 L Forearm', 'Bip01 L Hand')}
    miss = 0.0; slid = 0.0; d0 = np.zeros(len(ts))
    S_ = None
    for k, W in enumerate(W_):
        o = W[iX][:3, 3]; a = W[iX][:3, 1] / np.linalg.norm(W[iX][:3, 1])
        s = float(s_t[k]); slid = max(slid, abs(s - pre[k, 0]) * w[k])
        d0[k] = np.linalg.norm((W[iH] @ np.r_[g_loc, 1])[:3] - (o + a * s))
        Rc = ortho(W[iH][:3, :3]); ac = Rc @ a_loc
        at = a * SIGN
        Rt = minrot(ac, at) @ Rc
        Tw = (o + a * s) - Rt @ g_loc
        S0, E0, H0 = W[iU][:3, 3], W[iF][:3, 3], W[iH][:3, 3]
        L1, L2 = np.linalg.norm(E0 - S0), np.linalg.norm(H0 - E0)
        dv = Tw - S0; dist = np.linalg.norm(dv); dh = dv / dist
        # soft reach: near full extension the elbow angle races (jitter); past L - SOFT the reach eases towards L along an exponential
        Lm = L1 + L2 - 1e-4; ds = Lm - SOFT
        dc = dist if dist <= ds else Lm - SOFT * np.exp(-(dist - ds) / SOFT)
        dc = float(max(dc, abs(L1 - L2) + 1e-4)); miss = max(miss, (dist - dc) * w[k])
        pv = (E0 - S0) - dh * ((E0 - S0) @ dh); pv = pv / max(np.linalg.norm(pv), 1e-9)
        cA = (L1 ** 2 + dc ** 2 - L2 ** 2) / (2 * L1 * dc); sA = np.sqrt(max(1 - cA ** 2, 0))
        E1 = S0 + dh * L1 * cA + pv * L1 * sA; T1 = S0 + dh * dc
        Ru = minrot(E0 - S0, E1 - S0); RuW = Ru @ ortho(W[iU][:3, :3])
        H1 = S0 + Ru @ (H0 - S0); Rf = minrot(H1 - E1, T1 - E1); RfW = Rf @ Ru @ ortho(W[iF][:3, :3])
        Pc = ortho(W[m.parent[iU]][:3, :3])
        locs = {'Bip01 L UpperArm': Pc.T @ RuW, 'Bip01 L Forearm': RuW.T @ RfW, 'Bip01 L Hand': RfW.T @ Rt}
        for n, Rl in locs.items(): out[n].append(matrix_quaternion(Rl))
    TF = float(os.environ.get('IK_FADE', 0.5))
    fs = np.clip(1 - ts / TF, 0, 1); fs = 0.5 - 0.5 * np.cos(np.pi * fs)
    fe = np.clip(1 - (ts[-1] - ts) / TF, 0, 1); fe = 0.5 - 0.5 * np.cos(np.pi * fe)
    NEWQ = {}
    for n, Q in out.items():
        Q = np.array(Q)
        for k in range(1, len(Q)):
            if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
        if QSIG > 0: Q = ndimage.gaussian_filter1d(Q, QSIG, axis=0, mode='nearest'); Q /= np.linalg.norm(Q, axis=1, keepdims=True)
        sm = an.samplers[ch[(n, 'rotation')].sampler]; orig = acc(sm.output)
        assert len(orig) == len(ts)
        if ENDS:
            # the swing: the grip's correction at the first and last key (a Standing-like pose: small) carried as a constant local
            # offset that fades over IK_FADE seconds while MM9's own hand leaves the shaft and comes back (no IK chase: jitter)
            cj = lambda q: q * np.array([-1, -1, -1, 1])
            d0q, d1q = qmul(cj(orig[0]), Q[0]), qmul(cj(orig[-1]), Q[-1])
            new_ = []
            for k in range(len(ts)):
                q = qmul(orig[k], slerp(np.array([0, 0, 0, 1.0]), d0q, fs[k]))
                new_.append(qmul(q, slerp(np.array([0, 0, 0, 1.0]), d1q, fe[k])))
            NEWQ[n] = np.array(new_); put(sm.output, NEWQ[n])
        else:
            NEWQ[n] = np.array([slerp(orig[k], Q[k], w[k]) for k in range(len(ts))]); put(sm.output, NEWQ[n])
    # the hole's real distance from the shaft with the new arm keys: the fist closes only once the hand is on the shaft
    e = np.zeros(len(ts))
    for k in range(len(ts)):
        pose = m.sample(an.name, float(ts[k]))
        for n, Qn in NEWQ.items():
            j = ix[n]; trs = list(pose.get(j, m.rest[j])); trs[1] = Qn[k]; pose[j] = trs
        W = m.world(pose); o = W[iX][:3, 3]; a = W[iX][:3, 1] / np.linalg.norm(W[iX][:3, 1]); pv_ = (W[iH] @ np.r_[g_loc, 1])[:3] - o
        e[k] = np.linalg.norm(pv_ - a * (pv_ @ a))
    wf_ = np.clip((0.02 - e) / 0.015, 0, 1); wf_ = wf_ * wf_ * (3 - 2 * wf_)
    if ENDS: w = np.maximum(fs, fe)
    for n in FING:
        c_ = ch.get((n, 'rotation')); dq = P['gripL'].get(n)
        if c_ is None or dq is None: continue
        sm = an.samplers[c_.sampler]; orig = acc(sm.output); tg = qmul(rest_q(n), np.array(dq))
        tt = acc(sm.input)[:, 0]; wk = np.interp(tt, ts, wf_)
        put(sm.output, np.array([slerp(orig[k], tg, wk[k]) for k in range(len(orig))]))
    rep[an.name] = {'w': np.round(w, 3).tolist(), 'wf': np.round(wf_, 3).tolist(), 'hole_cm': np.round(e * 100, 1).tolist(), 'times': np.round(ts, 4).tolist(), 'max_w': round(float(w.max()), 2), 'reach_miss_cm': round(miss * 100, 2), 'slide_cm': round(slid * 100, 1)}
g.set_binary_blob(bytes(blob)); g.save(OUT)
json.dump(rep, open(HERE / 'work' / 'left_ik.json', 'w'))
print('LEFTIK', {k: (v['max_w'], v['reach_miss_cm'], v['slide_cm']) for k, v in rep.items()})
