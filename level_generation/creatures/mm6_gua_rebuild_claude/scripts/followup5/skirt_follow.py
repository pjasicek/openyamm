#!/usr/bin/env python3
"""Mail hem in the gaits (follow-up 5, user 2026-11-12: "the hem flares like a skirt and the legs pass through it").
Cause (skirt_keys.py, 2026-11-11): every sector of the six-hinge ring took a running maximum over 0.17 s, a 4-6 cm margin
and 85 % of its neighbours' swing, so in Walking/Walk2/Jog/Running all six hinges stood at 58-68 deg the whole cycle: a
bell; at the 68 deg cap the knees still came through in front.
Fix, Walking, Walk2, Jog and Running only (every other clip keeps its keys): each hinge follows the thigh under it frame by
frame (closed-form least swing that keeps that thigh MARGIN under the cloth, sampled at 60 fps), a light circular Gaussian
instead of the hold, a small neighbour share (the ring stays closed without lifting the sides), and the hinges may also swing
INWARD (negative) up to a limit so a panel whose thigh has gone back hangs onto it instead of standing off. Thighs above
the hem only: points below the hem (depth > the hem length) do not lift the cloth.
Args: <in glb> <out glb> [report json]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from glbtool import Glb, Model, repack
IN, OUT = sys.argv[1:3]
CLIPS = {'Walking': 0.018, 'Walk2': 0.02, 'Jog': 0.022, 'Running': 0.022}     # margin (m) per clip
SIGMA, SHARE, MAXDEG, MINDEG, SECTOR = 0.025, 0.35, 60.0, -10.0, 0.80
RING = ['Skirt_FR', 'Skirt_FL', 'Skirt_SL', 'Skirt_BL', 'Skirt_BR', 'Skirt_SR']
NB = {0: (1, 5), 1: (0, 2), 2: (1, 3), 3: (2, 4), 4: (3, 5), 5: (4, 0)}
g = Glb(IN); m = Model(g); doc = g.json
names = [n.get('name') for n in doc['nodes']]
jn = [names[j] for j in m.joints]
pr = m.primitives[0]; J, W = pr['joints'], pr['weights']
SP = names.index('Bip01 Spine')
w0 = m.world({}); S0i = np.linalg.inv(w0[SP])
rest = m.skinned_positions(w0)[0][0]
legv = {s: np.where((np.isin(J, [i for i, n in enumerate(jn) if f'{s} Thigh' in n or f'{s} Calf' in n]) * W).sum(1) > 0.5)[0] for s in 'LR'}
legall = np.r_[legv['L'], legv['R']]
spine_up = S0i[:3, :3] @ np.array([0, 1.0, 0])
hinge = {}
cen = np.mean([w0[names.index(n)][:3, 3] for n in RING], 0)
for n in RING:
    i = names.index(n); p = w0[i][:3, 3]
    d = p - cen; d[1] = 0; d /= np.linalg.norm(d)
    if n[-2] in 'FB': d = np.array([0, 0, np.sign(d[2])])
    nn = S0i[:3, :3] @ d; ax = np.cross(-spine_up, nn); ax /= np.linalg.norm(ax)
    wd = p - cen; wd[1] = 0; wd /= np.linalg.norm(wd)
    hinge[n] = dict(i=i, p=(S0i @ np.r_[p, 1])[:3], n=nn, ax=ax, sec=S0i[:3, :3] @ wd, side='L' if n[-1] == 'L' else 'R')
sk = [i for i, n in enumerate(jn) if n.startswith('Skirt_')]
sv = np.where((np.isin(J, sk) * W).sum(1) > 0.01)[0]
restS = (S0i @ np.c_[rest, np.ones(len(rest))].T).T[:, :3][sv]
cS = np.mean([hinge[x]['p'] for x in RING], 0)
for nm in RING:
    H = hinge[nm]; v = restS - H['p']; dep = -(v @ spine_up); rad = v @ H['n']
    sc = (restS - cS) - np.outer((restS - cS) @ spine_up, spine_up); sn = np.linalg.norm(sc, axis=1)
    ok = (sc @ H['sec']) / np.maximum(sn, 1e-6) > np.cos(SECTOR)
    H['len'] = float(dep[ok].max())
    bins = np.linspace(0.0, H['len'], 9); surf = np.full(8, np.nan)
    for k in range(8):
        mm = ok & (dep >= bins[k]) & (dep < bins[k + 1])
        if mm.any(): surf[k] = rad[mm].max()
    idx = np.where(~np.isnan(surf))[0]
    H['surf'] = (0.5 * (bins[:-1] + bins[1:]), np.interp(np.arange(8), idx, surf[idx]))
print('HEM length below hinges', {k: round(hinge[k]['len'], 3) for k in RING})


def need(y, H, margin):
    """Swing (rad, + outward) that puts every thigh point under this hinge's panel `margin` inside the cloth; the most
    negative (inward) swing allowed when nothing pushes is returned as the inward bound."""
    c = cS; v = y - H['p']; depth = -(v @ spine_up); rad = v @ H['n']
    sc = (y - c) - np.outer((y - c) @ spine_up, spine_up); sn = np.linalg.norm(sc, axis=1)
    ok = (sn > 1e-6) & (depth > 0.01) & ((sc @ H['sec']) / np.maximum(sn, 1e-6) > np.cos(SECTOR))
    # a point counts while the swung hem still reaches its depth: along the cloth, length >= hypot(depth, rad)
    ok &= np.hypot(depth, np.maximum(rad, 0)) < H['len'] + 0.01
    if not ok.any(): return -1.0
    R = np.interp(depth[ok], H['surf'][0], H['surf'][1])
    return float((np.arctan2(rad[ok] + margin, depth[ok]) - np.arctan2(R, depth[ok])).max())


def rot_q(ax, a):
    s = np.sin(a / 2); return np.array([ax[0] * s, ax[1] * s, ax[2] * s, np.cos(a / 2)])


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


# --- posed-mesh test (skirt_gate.py's: outer cloth faces, leg points outside a face they project into) ---
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared'))
from detached_parts_audit import closest_on_triangles  # noqa: E402
TRI = np.asarray(pr['triangles']).reshape(-1, 3)
swv = (np.isin(J, sk) * W).sum(1)
FACE = np.where((swv[TRI] > 0.01).all(1))[0]
ft0 = rest[TRI[FACE]]; n0 = np.cross(ft0[:, 1] - ft0[:, 0], ft0[:, 2] - ft0[:, 0]); n0 /= np.maximum(np.linalg.norm(n0, axis=1, keepdims=True), 1e-12)
FACE = FACE[((n0 * (ft0.mean(1) * [1, 0, 1])).sum(1) > 0) & (np.abs(n0[:, 1]) < 0.6)]
HW = np.zeros((len(rest), 6))                                   # per vertex weight of each hinge
for k, nm in enumerate(RING):
    ji = jn.index(nm); HW[:, k] = (W * (J == ji)).sum(1)
FHW = HW[TRI[FACE]].mean(1)


def rv_q(rv):
    a = float(np.linalg.norm(rv))
    return np.array([0, 0, 0, 1.0]) if a < 1e-9 else rot_q(rv / a, a)


def pose(clip, t, RV):
    """Posed vertices and world matrices with the hinges at rotation vectors RV (6, 3), in the Spine (parent) frame."""
    loc = m.sample(clip, t)
    for k, nm in enumerate(RING):
        H = hinge[nm]; q0 = np.array(doc['nodes'][H['i']].get('rotation', [0, 0, 0, 1]), float)
        tr = loc.get(H['i'], [x.copy() for x in m.rest[H['i']]]); tr[1] = qmul(rv_q(RV[k]), q0); loc[H['i']] = tr
    w = m.world(loc)
    return m.skinned_positions(w)[0][0], w


def through(clip, t, RV, margin=0.006):
    """Extra rotation vector per hinge (6, 3) that the leg points still outside the cloth ask for at this pose: each
    hinge weighting the face a point comes through swings that cloth out along the face normal."""
    x, w = pose(clip, t, RV); ft = x[TRI[FACE]]
    c_ = ft.mean(1); n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
    q = x[legall]; _, near = cKDTree(c_).query(q, k=24); pts = np.repeat(q, 24, 0)
    qq, _ = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
    dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(q))
    fid = near[r, b]; cp = qq.reshape(*near.shape, 3)[r, b]; s_ = np.einsum('ij,ij->i', q - cp, n_[fid]); dist = dd[r, b]
    th = (s_ > -margin) & (s_ > 0.98 * dist - margin) & (dist < 0.2)
    out = np.zeros((6, 3)); Rs = w[SP][:3, :3].T
    for i in np.where(th)[0]:
        wv = FHW[fid[i]]
        if wv.sum() < 0.5: continue                                      # the belt band: hinges barely move it
        N = Rs @ n_[fid[i]]; ax = np.cross(-spine_up, N); na = np.linalg.norm(ax)
        if na < 0.2: continue                                            # a horizontal face: no swing helps
        mag = (s_[i] + margin) / 0.09 * wv / wv.sum()                     # 9 cm: the cloth's lever at hem depth
        for k in range(6):
            if mag[k] > np.linalg.norm(out[k]): out[k] = ax / na * mag[k]
    return out


rep = {}
for an in doc['animations']:
    clip = an['name']
    if clip not in CLIPS: continue
    dur = m.clip_times(clip)[-1]; n = int(round(dur * 60)); T = np.linspace(0, dur, n + 1); dt = T[1]
    A = np.zeros((len(T), 6))
    for f, t in enumerate(T):
        w = m.world(m.sample(clip, float(t))); x = m.skinned_positions(w)[0][0]; Si = np.linalg.inv(w[SP])
        y = (Si @ np.c_[x[legall], np.ones(len(legall))].T).T[:, :3]
        for k, nm in enumerate(RING):
            A[f, k] = need(y, hinge[nm], CLIPS[clip])
    A = np.clip(A, np.radians(MINDEG), np.radians(MAXDEG))
    S = gaussian_filter1d(A[:-1], SIGMA / dt, axis=0, mode='wrap'); S = np.r_[S, S[:1]]
    S2 = S.copy()
    for k, (a, b) in NB.items():
        S2[:, k] = np.maximum(S[:, k], SHARE * np.maximum(S[:, a], S[:, b]))
    # second pass on the posed mesh: wherever a thigh still comes through the outer cloth (skirt_gate.py's test), the
    # hinges weighting the face it comes through swing out a little more, until clear; then a 3-frame hold and a light blur
    RV = S2[:, :, None] * np.array([hinge[nm]['ax'] for nm in RING])[None]
    for f, t in enumerate(T[:-1]):
        for it in range(14):
            push = through(clip, float(t), RV[f])
            if not push.any(): break
            RV[f] += push
            mg = np.linalg.norm(RV[f], axis=1, keepdims=True); RV[f] *= np.minimum(1, np.radians(MAXDEG) / np.maximum(mg, 1e-9))
    RV[-1] = RV[0]; core = RV[:-1]; mg = np.linalg.norm(core, axis=2)
    pick = np.argmax([np.roll(mg, k, 0) for k in (-1, 0, 1)], 0)                   # 3-frame hold by magnitude
    H3 = np.choose(pick[..., None], [np.roll(core, k, 0) for k in (-1, 0, 1)])
    RV = gaussian_filter1d(H3, 1.0, axis=0, mode='wrap'); RV = np.r_[RV, RV[:1]]
    S2 = np.linalg.norm(RV, axis=2)
    an['channels'] = [c for c in an['channels'] if not (names[c['target']['node']].startswith('Skirt_') and c['target']['path'] == 'rotation')]
    tacc = g.append_accessor(T.astype(np.float32), 'SCALAR')
    for k, nm in enumerate(RING):
        H = hinge[nm]; q0 = np.array(doc['nodes'][H['i']].get('rotation', [0, 0, 0, 1]), float)
        Q = np.array([qmul(rv_q(v), q0) for v in RV[:, k]]); Q /= np.linalg.norm(Q, axis=1, keepdims=True)
        for j in range(1, len(Q)):
            if Q[j] @ Q[j - 1] < 0: Q[j] = -Q[j]
        an['samplers'].append(dict(input=tacc, output=g.append_accessor(Q.astype(np.float32), 'VEC4'), interpolation='LINEAR'))
        an['channels'].append(dict(sampler=len(an['samplers']) - 1, target=dict(node=H['i'], path='rotation')))
    rep[clip] = {RING[k]: [round(float(np.degrees(S2[:, k].min())), 1), round(float(np.degrees(S2[:, k].mean())), 1), round(float(np.degrees(S2[:, k].max())), 1)] for k in range(6)}
    print('SKIRT', clip, 'min/mean/max deg', rep[clip], flush=True)
repack(g); g.write(OUT)
if len(sys.argv) > 3: json.dump(rep, open(sys.argv[3], 'w'), indent=1)
print('SKIRT written', OUT)
