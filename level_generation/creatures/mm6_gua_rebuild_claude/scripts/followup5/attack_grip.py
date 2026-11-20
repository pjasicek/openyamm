#!/usr/bin/env python3
"""Attack and Attack2 arms (follow-up 5, user 2026-11-12): the left hand does not hold the shaft (its fingers stay open
beside the pole) and the right wrist is twisted like a candy wrapper.

Left hand. MM9's Hattack1/Hattack2 bring the left mitten near the pole (palm 2-8 cm from the shaft axis) but our MPFB hand
keeps MM9's open mitten curl. Over the stretch where the hand is near the shaft (window per clip below, eased in and out)
the left arm is solved onto the shaft: the hand is turned (least rotation from the animated hand) so its grip channel
(along the knuckle line, under the proximal phalanges, measured on our own left hand) lies on the shaft axis, at the point
of the shaft nearest the animated hand, kept GAP m behind the right fist; the upper arm and forearm reach it by two-bone
IK in the animated elbow plane; the fingers and thumb close on the shaft: each chain curls about its own joints (the
mirrored right-grip axes) as far as it goes without entering the shaft (numeric search on the bind hand), the fist
held for the whole window.

Wrists. Hattack1 turns the right hand ~120 deg about the forearm beyond its Standing turn (MM9 data: their weapon rides
the hand), all of it at the wrist: the candy-wrapper twist. The extra turn over the clip's first frame is shared:
TWIST_SHARE of it goes to the forearm (rolling about its own axis, so the hand origin does not move), the hand is turned
back by the same amount, so the hand, the fist and the halberd keep their exact world pose. Same for the left arm after
the grip solve. Only Attack and Attack2 are touched; the forearm half-joint helpers are re-keyed by helper_keys.py after.
Args: <in body glb> <halberd glb (Xbase space)> <out glb> [report json]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from glbtool import Glb, Model, repack
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
from glb_pose import matrix_quaternion, quaternion_matrix, slerp  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared'))
from detached_parts_audit import closest_on_triangles  # noqa: E402

IN, HAL, OUT = sys.argv[1:4]
WINDOWS = {'Attack': (0.20, 0.27, 0.47, 0.54), 'Attack2': (0.27, 0.34, 0.43, 0.49)}   # ease in from, full, full until, out by (s)
GAP, TWIST_SHARE, SKIN, CLEAR, NROLL = 0.16, 0.6, 0.004, 0.07, 4
FINGERS = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
g = Glb(IN); doc = g.json; m = Model(g)
names = [n.get('name') for n in doc['nodes']]; N = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in m.joints]
w0 = m.world({})
XB = N['Xbase']

# ---- the shaft in Xbase space ---------------------------------------------------------------------------------------
hm = Model(Glb(HAL)); V = np.concatenate([p['positions'] for p in hm.primitives])
c = V.mean(0); ax = np.linalg.svd(V - c)[2][0]; t = (V - c) @ ax
if np.ptp(V[t > t.max() - 0.3] - c, 0).max() < np.ptp(V[t < t.min() + 0.3] - c, 0).max(): ax = -ax; t = -t
shaft = V[(t > t.min() + 0.1) & (t < t.max() - 0.45)]; P0 = shaft.mean(0)
AX = np.linalg.svd(shaft - P0)[2][0]; AX *= np.sign(AX @ ax)
RAD = float(np.median(np.linalg.norm((shaft - P0) - np.outer((shaft - P0) @ AX, AX), axis=1)))
S_BUTT = float(((V - P0) @ AX).min())
print('GRIP shaft radius %.4f m, butt at s=%.3f' % (RAD, S_BUTT))


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def axang(axis, a):
    axis = np.asarray(axis, float); axis = axis / np.linalg.norm(axis); s = np.sin(a / 2)
    return np.array([axis[0] * s, axis[1] * s, axis[2] * s, np.cos(a / 2)])


def q_between(u, v):
    u = u / np.linalg.norm(u); v = v / np.linalg.norm(v); cr = np.cross(u, v); d = float(u @ v)
    if d < -0.9999:
        o = np.cross(u, [1, 0, 0]); o = o if np.linalg.norm(o) > 1e-3 else np.cross(u, [0, 1, 0])
        return axang(o, np.pi)
    q = np.r_[cr, 1 + d]; return q / np.linalg.norm(q)


def mirror_q(q):                                                    # Bip01 R <-> L local rotation
    return np.array([-q[0], q[1], -q[2], q[3]])


# ---- left fist on the bind hand ----------------------------------------------------------------------------------
poses = json.load(open(Path(__file__).resolve().parents[2] / 'work' / 'hand_poses.json'))
GRIP = {k.replace(' R ', ' L '): mirror_q(np.array(v, float)) for k, v in poses['grip'].items()}
pr0 = m.primitives[0]; Jv, Wv = pr0['joints'], pr0['weights']
dom = np.array([jn[j] for j in Jv[np.arange(len(Jv)), Wv.argmax(1)]])
FV = {f: np.where(np.char.startswith(dom.astype(str), f'Bip01 L {f}'))[0] for f in FINGERS}
PALM = np.where(dom == 'Bip01 L Hand')[0]
TIP = {f: np.where(dom == f'Bip01 L {f}3')[0] for f in FINGERS}
ARMV = np.where(np.isin(dom, ['Bip01 L Forearm', 'Bip01 L Forearm_H', 'Bip01 L Hand']))[0]
RFV = np.where(np.isin(dom, ['Bip01 R Forearm', 'Bip01 R Forearm_H']))[0]
_lt = np.asarray(pr0['triangles']).reshape(-1, 3)
LTRI = _lt[np.isin(_lt, np.where(np.char.startswith(dom.astype(str), 'Bip01 L ') & ~np.char.startswith(dom.astype(str), 'Bip01 L UpperArm')
                                 & ~np.char.startswith(dom.astype(str), 'Bip01 L Clavicle') & ~np.char.startswith(dom.astype(str), 'Bip01 L Thigh')
                                 & ~np.char.startswith(dom.astype(str), 'Bip01 L Calf') & ~np.char.startswith(dom.astype(str), 'Bip01 L Foot')
                                 & ~np.char.startswith(dom.astype(str), 'Bip01 L Toe'))[0]).all(1)]
BODY = np.where(~np.char.startswith(dom.astype(str), 'Bip01 L ') | np.char.startswith(dom.astype(str), 'Bip01 L Thigh')
                | np.char.startswith(dom.astype(str), 'Bip01 L Calf') | np.char.startswith(dom.astype(str), 'Bip01 L Foot'))[0]
BODY = BODY[~np.isin(dom[BODY], [f'Bip01 R {k}{j}' for k in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky') for j in (1, 2, 3)] + ['Bip01 R Hand'])]
H = N['Bip01 L Hand']; Hw0 = w0[H]
J = lambda n: w0[N[n]][:3, 3]
k_ = J('Bip01 L Index1') - J('Bip01 L Pinky1'); k_ /= np.linalg.norm(k_)
f_ = J('Bip01 L Middle1') - Hw0[:3, 3]; f_ -= (f_ @ k_) * k_; f_ /= np.linalg.norm(f_)
n_ = np.cross(k_, f_)


BASE = (1.0, 1.25, 0.9)                                             # flexion of joints 1, 2, 3 per unit of curl (rad)
TBASE = (0.35, 0.7, 0.8)                                            # thumb joints about the shaft axis


def finger_pose(scales, nrm=None):
    """Bind pose with the left fingers flexed about their own anatomical axes (finger direction x palm normal) by
    scales[f] units, the thumb turned about the knuckle line (the shaft's direction) by scales['Thumb'] (signed)."""
    nrm = n_ if nrm is None else nrm
    loc = {}
    for f in FINGERS:
        sc = scales.get(f, 0.0)
        for j in (1, 2, 3):
            i = N[f'Bip01 L {f}{j}']; Rw = w0[i][:3, :3]
            if f == 'Thumb':
                axw = k_; ang = sc * TBASE[j - 1]
            else:
                nxt = N[f'Bip01 L {f}{j + 1}'] if f'Bip01 L {f}{j + 1}' in N else None
                d = (w0[nxt][:3, 3] - w0[i][:3, 3]) if nxt is not None else (w0[i][:3, 3] - w0[N[f'Bip01 L {f}{j - 1}']][:3, 3])
                d /= np.linalg.norm(d); axw = np.cross(d, nrm); axw /= np.linalg.norm(axw); ang = sc * BASE[j - 1]
            loc[i] = [m.rest[i][0].copy(), qmul(m.rest[i][1], axang(Rw.T @ axw, ang)), m.rest[i][2].copy()]
    return loc


best = None
for u in np.arange(-0.01, 0.061, 0.01):                              # channel position in the hand: along the fingers (u)
    for v in np.arange(0.0, 0.061, 0.01):                            # and toward the palm side (v) from the middle knuckle
        cen = J('Bip01 L Middle1') + f_ * u + n_ * v
        dist = lambda X: np.linalg.norm((X - cen) - np.outer((X - cen) @ k_, k_), axis=1)
        near = PALM[np.abs((pr0['positions'][PALM] - cen) @ k_) < 0.05]
        dp = dist(pr0['positions'][near]).min()
        if dp < RAD + SKIN or dp > RAD + 0.012: continue                 # the shaft rests on the palm, not in it
        sc = {}; score = dp - RAD; valid = True
        for f in FINGERS:
            cands = [(sg, ok) for sg in ((1, -1) if f == 'Thumb' else (1,)) for ok in [None]]
            res = []
            for sg, _ in cands:
                ok = None
                for s_ in np.arange(-0.3, 1.81, 0.1):
                    X = m.skinned_positions(m.world(finger_pose({f: sg * s_})))[0][0][FV[f]]
                    if dist(X).min() < RAD + SKIN: break
                    ok = s_
                if ok is None: continue
                X = m.skinned_positions(m.world(finger_pose({f: sg * ok})))[0][0][TIP[f]]
                res.append((float(np.clip(dist(X).min() - RAD, 0, 0.05)), sg * ok))
            if not res: valid = False; break
            gap, val = min(res); sc[f] = round(float(val), 2); score += gap
        if valid and (best is None or score < best[0]): best = (score, u, v, sc, cen)
score, U, VV, SCALE, CEN = best
print('GRIP left fist: channel %.0f mm along the fingers, %.0f mm palm-side of the middle knuckle; curl scales %s; mean gap %.1f mm' % (
    U * 1000, VV * 1000, {f: round(s, 1) for f, s in SCALE.items()}, score / 6 * 1000))
FIST = {N[nm]: q[1] for nm, q in ((nm, finger_pose(SCALE)[N[nm]]) for nm in GRIP)}
RH0i = np.linalg.inv(Hw0)
A_LOC = RH0i[:3, :3] @ k_; C_LOC = (RH0i @ np.r_[CEN, 1])[:3]          # grip channel in the left hand's frame

# ---- per clip ---------------------------------------------------------------------------------------------------
ARM = {s: [N[f'Bip01 {s} UpperArm'], N[f'Bip01 {s} Forearm'], N[f'Bip01 {s} Hand']] for s in 'LR'}
R_GRIP_S = None


BTRI = np.asarray(pr0['triangles']).reshape(-1, 3); BTRI = BTRI[np.isin(BTRI, BODY).all(1)]


def signed_clear(pts, X, tris=None):
    """distance of each point to the body surface (the left arm and the right fist aside), negative when behind the
    nearest face (inside)"""
    T = X[BTRI if tris is None else tris]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    k = 40; _, near = cKDTree((a + b + c) / 3).query(pts, k=k); near = near.reshape(len(pts), -1)
    q, _ = closest_on_triangles(np.repeat(pts, k, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(np.repeat(pts, k, 0) - q, axis=1).reshape(near.shape); bi = d.argmin(1); r = np.arange(len(pts))
    side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[r, bi], n[near[r, bi]])
    return np.where(side < 0, -d[r, bi], d[r, bi])


def smooth01(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def twist_about_x(q):
    return 2 * np.arctan2(q[0], q[3])


def ik(w, o_b, R_b, sw=0.0):
    U_, F_, Hh = ARM['L']
    S_, E_, W_ = w[U_][:3, 3], w[F_][:3, 3], w[Hh][:3, 3]
    L1, L2 = np.linalg.norm(E_ - S_), np.linalg.norm(W_ - E_)
    d = np.clip(np.linalg.norm(o_b - S_), abs(L1 - L2) + 1e-4, L1 + L2 - 1e-4)
    nrm = np.cross(E_ - S_, W_ - E_); nrm = nrm / np.linalg.norm(nrm) if np.linalg.norm(nrm) > 1e-6 else w[F_][:3, 2]
    cur_in = np.arccos(np.clip((E_ - S_) @ (W_ - E_) / (L1 * L2), -1, 1))
    want_in = np.pi - np.arccos(np.clip((L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2), -1, 1))
    qb = axang(nrm, want_in - cur_in)
    Rf = quaternion_matrix(qb) @ w[F_][:3, :3]
    W1 = E_ + quaternion_matrix(qb) @ (W_ - E_)
    qs = q_between(W1 - S_, o_b - S_)
    Ru = quaternion_matrix(qs) @ w[U_][:3, :3]; Rf = quaternion_matrix(qs) @ Rf
    if sw:                                                             # swivel the elbow about the shoulder-wrist line
        Rs = quaternion_matrix(axang(o_b - S_, sw)); Ru = Rs @ Ru; Rf = Rs @ Rf
    Pu = w[m.parent[U_]][:3, :3]
    qh = matrix_quaternion(Rf.T @ R_b)
    return (matrix_quaternion(Pu.T @ Ru), matrix_quaternion(Ru.T @ Rf), qh), np.linalg.norm(o_b - S_) / (L1 + L2)


def solve_frame(loc, b, s_hold, tw_ref):
    """Left arm onto the shaft with blend b: the roll of the hand about the shaft and the sign are chosen for the least
    wrist turn against the forearm (tw_ref: the clip's own first-frame turn), the hold point slides toward the shoulder
    until the arm reaches it."""
    w = m.world(loc); M = w[XB]
    Pw = (M @ np.r_[P0, 1])[:3]; Aw = M[:3, :3] @ AX
    U_, F_, Hh = ARM['L']; W_ = w[Hh][:3, 3]; Rcur = w[Hh][:3, :3]
    s_sh = float((w[U_][:3, 3] - Pw) @ Aw)
    best = None
    for sg in (1, -1):
        R0 = quaternion_matrix(q_between(Rcur @ A_LOC, sg * Aw)) @ Rcur
        for psi in np.radians(np.arange(0, 360, 10)):
            Rw = quaternion_matrix(axang(Aw, psi)) @ R0
            for ds in np.linspace(0, 1, 11):
                sh = s_hold + ds * (s_sh - s_hold)
                o = Pw + sh * Aw - Rw @ C_LOC
                o_b = W_ + b * (o - W_); R_b = quaternion_matrix(slerp(matrix_quaternion(Rcur), matrix_quaternion(Rw), b))
                qs, reach = ik(w, o_b, R_b)
                if reach < 0.97: break
            tw = twist_about_x(qs[2]); dtw = abs((tw - tw_ref + np.pi) % (2 * np.pi) - np.pi)
            cost = dtw + 0.5 * abs(psi if psi <= np.pi else 2 * np.pi - psi) + (5 if reach >= 0.97 else 0) + 2 * ds
            best = (best or []) + [(cost, qs, o_b, R_b)]
    best.sort(key=lambda x: x[0])
    return best[:NROLL]


rep = {}
for an in doc['animations']:
    clip = an['name']
    if clip not in WINDOWS: continue
    dur = m.clip_times(clip)[-1]; T = np.linspace(0, dur, int(round(dur * 60)) + 1)
    t0, t1, t2, t3 = WINDOWS[clip]
    B = np.minimum(smooth01((T - t0) / (t1 - t0)), smooth01((t3 - T) / (t3 - t2)))
    LOC = [m.sample(clip, float(t)) for t in T]
    # where along the shaft the left hand is, and where the right fist is
    sL, sR = [], []
    for loc in LOC:
        w = m.world(loc); M = w[XB]; Pw = (M @ np.r_[P0, 1])[:3]; Aw = M[:3, :3] @ AX
        cen = w[ARM['L'][2]] @ np.r_[C_LOC, 1]
        sL.append(float((cen[:3] - Pw) @ Aw))
        rk = 0.5 * (w[N['Bip01 R Index1']][:3, 3] + w[N['Bip01 R Pinky1']][:3, 3])
        sR.append(float((rk - Pw) @ Aw))
    sL = np.array(sL); sR = np.array(sR)
    hold = np.clip(sL, S_BUTT + 0.12, sR - GAP)
    win = B > 0
    # the hold must leave room for the hand: the shaft point CLEAR m from the body (the left arm and the right fist aside)
    for f in np.where(win)[0]:
        cand = np.arange(S_BUTT + 0.12, sR[f] - GAP + 1e-6, 0.01)
        if not len(cand): continue
        clear = np.full(len(cand), np.inf)
        for dt in (-1 / 120, 0.0, 1 / 120):                            # between the keys too: the shaft sweeps fast
            w = m.world(m.sample(clip, float(np.clip(T[f] + dt, 0, dur)))); M = w[XB]
            Pw = (M @ np.r_[P0, 1])[:3]; Aw = M[:3, :3] @ AX
            clear = np.minimum(clear, signed_clear(Pw + np.outer(cand, Aw), m.skinned_positions(w)[0][0]))
        ok = cand[clear >= CLEAR]
        hold[f] = ok[np.argmin(np.abs(ok - hold[f]))] if len(ok) else cand[np.argmax(clear)]
    if win.sum() > 3:                                                   # slide smoothly; a forward move is held a little
        hold[win] = gaussian_filter1d(maximum_filter1d(hold[win], 9, mode='nearest'), 2.0, mode='nearest')
    newL = {i: [] for i in ARM['L']}; fing = {i: [] for i in FIST}
    tw_ref = twist_about_x(LOC[0].get(ARM['L'][2], m.rest[ARM['L'][2]])[1])
    # pass 1: hand target per frame and the elbow swivel that keeps the forearm and hand out of the body
    TGT = {}; SW = np.zeros(len(T))
    for f, loc in enumerate(LOC):
        if B[f] <= 0: continue
        w = m.world(loc); best = None
        for c0, qs, o_b, R_b in solve_frame(loc, B[f], hold[f], tw_ref):
            for sw in np.radians(np.arange(-75, 76, 15)):
                q3, _ = ik(w, o_b, R_b, sw); l2 = dict(loc)
                for i, q in zip(ARM['L'], q3): l2[i] = [loc.get(i, m.rest[i])[0], q, np.ones(3)]
                X = m.skinned_positions(m.world(l2))[0][0]
                dep = max(0.0, -float(signed_clear(X[ARMV], X).min()), -float(signed_clear(X[RFV], X, LTRI).min()))
                cost = dep + 0.0002 * abs(np.degrees(sw)) + 0.004 * c0                # 1 cm of depth ~ 2.5 rad of extra wrist turn
                if best is None or cost < best[0]: best = (cost, sw, o_b, R_b)
        TGT[f] = (best[2], best[3])
        SW[f] = best[1]
    if (B > 0).sum() > 3: SW[B > 0] = gaussian_filter1d(SW[B > 0], 2.0, mode='nearest')
    for f, loc in enumerate(LOC):
        if B[f] > 0:
            (qu, qf, qh), _ = ik(m.world(loc), TGT[f][0], TGT[f][1], SW[f])
        else:
            qu, qf, qh = (loc.get(i, m.rest[i])[1] for i in ARM['L'])
        for i, q in zip(ARM['L'], (qu, qf, qh)): newL[i].append(q); loc[i] = [loc.get(i, m.rest[i])[0], q, np.ones(3)]
        for i, qg in FIST.items():
            q0 = loc.get(i, m.rest[i])[1]; q = slerp(q0, qg, B[f]); fing[i].append(q); loc[i] = [loc.get(i, m.rest[i])[0], q, np.ones(3)]
    # twist share, both arms
    for s in 'LR':
        Fi, Hi = ARM[s][1], ARM[s][2]
        tw = np.unwrap([twist_about_x(loc.get(Hi, m.rest[Hi])[1]) for loc in LOC])
        extra = tw - tw[0]; phi = TWIST_SHARE * extra
        for f, loc in enumerate(LOC):
            qf = qmul(loc.get(Fi, m.rest[Fi])[1], axang([1, 0, 0], phi[f])); qh = qmul(axang([1, 0, 0], -phi[f]), loc.get(Hi, m.rest[Hi])[1])
            loc[Fi] = [loc.get(Fi, m.rest[Fi])[0], qf, np.ones(3)]; loc[Hi] = [loc.get(Hi, m.rest[Hi])[0], qh, np.ones(3)]
        rep.setdefault(clip, {})[f'{s} wrist turn beyond the first frame, deg'] = [round(float(np.degrees(extra.min())), 0), round(float(np.degrees(extra.max())), 0)]
        rep[clip][f'{s} wrist after the share, deg'] = round(float(np.degrees(np.abs(extra - phi).max())), 0)
    # write: every touched node gets a fresh 60 fps rotation channel
    touched = ARM['L'] + [ARM['R'][1], ARM['R'][2]] + list(FIST)
    an['channels'] = [c for c in an['channels'] if not (c['target']['node'] in touched and c['target']['path'] == 'rotation')]
    tacc = g.append_accessor(T.astype(np.float32), 'SCALAR')
    for i in touched:
        Q = np.array([loc.get(i, m.rest[i])[1] for loc in LOC], float); Q /= np.linalg.norm(Q, axis=1, keepdims=True)
        for j in range(1, len(Q)):
            if Q[j] @ Q[j - 1] < 0: Q[j] = -Q[j]
        an['samplers'].append(dict(input=tacc, output=g.append_accessor(Q.astype(np.float32), 'VEC4'), interpolation='LINEAR'))
        an['channels'].append(dict(sampler=len(an['samplers']) - 1, target=dict(node=i, path='rotation')))
    # check: left grip channel to the shaft axis in the full window
    err = []
    for f, loc in enumerate(LOC):
        if B[f] < 0.999: continue
        w = m.world(loc); M = w[XB]; Pw = (M @ np.r_[P0, 1])[:3]; Aw = M[:3, :3] @ AX
        cen = (w[ARM['L'][2]] @ np.r_[C_LOC, 1])[:3]; d = cen - Pw; err.append(np.linalg.norm(d - (d @ Aw) * Aw))
    rep[clip]['left grip on the shaft axis, max mm'] = round(1000 * max(err), 1) if err else None
    rep[clip]['left hand hold, s along the shaft'] = [round(float(hold[win].min()), 3), round(float(hold[win].max()), 3)]
    print('GRIP', clip, rep[clip], flush=True)
repack(g); g.write(OUT)
if len(sys.argv) > 4: json.dump(rep, open(sys.argv[4], 'w'), indent=1)
print('GRIP written', OUT)
