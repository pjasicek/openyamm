#!/usr/bin/env python3
"""Cloak chains `Cloak_<k>_<j>` (rig_thf.py, work/rig_v1.blend.cloak.json) keyed per clip on the clip's own key times. Each frame is solved on its own
(no simulation state, so loops close and one-shots start where the body's eased start pose puts them), as a small position-based problem on the
chain joints:
1. Target: each segment hangs between rigid-with-Spine3 and plumb (the rest drape turned by the heading only), more plumb further down
   (GRAV); a torso tilted past 35-70 deg (death) takes the rigid drape. Locomotion loops trail the cloak backwards (TRAIL deg).
2. ITER rounds of: push joints and segment midpoints out of capsules on the legs, feet, arms, hands and hips (radius + MARGIN, but never
   more than the joint's own clearance at the bind pose: the drawn cloak clears the body there, the chain line runs mid-thickness);
   keep neighbouring columns' joints within LAT_MIN..LAT_MAX of their rest spacing (the cloth between two columns cannot tear: the installed
   cloak's verlet chains tore in Sprint); exact segment lengths from the root down; above the floor.
3. Joint paths smoothed in the Spine3 frame (Gaussian SIGMA_T, circular on loops), lengths restored.
4. Bone rotations: least turn from the Spine3-rigid rest direction to the solved direction.
Dead holds Death's last frame. Args: <in glb> <out glb> <cloak json> <report json>"""
import json, sys, math
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion
IN, OUT, CJ, REP = sys.argv[1:5]
GRAV = [0.45, 0.75, 0.9, 0.95]
TRAIL = {'Walking': 4.0, 'Walk2': 5.0, 'Jog': 12.0, 'Running': 16.0}
LOOPS = ('Standing', 'Walking', 'Running', 'Walk2', 'Jog')
ITER, LAT_MAX, LAT_MIN, SIGMA_T = 12, 1.22, 0.85, 0.03
FLOOR = float(sys.argv[5]) if len(sys.argv) > 5 else -0.03
LAND = 0.62                                                      # die1 lands about here (body on the floor)
import os
FALLFLOOR = float(os.environ.get('FALLFLOOR', -0.08))                  # while falling the hem may dip this far under the floor
FALLSLACK = float(os.environ.get('FALLSLACK', 0.16))                    # falling: cloak vertices at most this far under the body's lowest point
ONLY = [x for x in os.environ.get('ONLY', '').split(',') if x]      # under the corpse the cloak may sink this far (hidden by the body)
MARGIN = {'leg': 0.02, 'arm': 0.015, 'hip': 0.02}
RAD = {'Thigh': 0.075, 'Calf': 0.065, 'UpperArm': 0.055, 'Forearm': 0.045}   # calf: the boot shaft
g = Glb(Path(IN)); m = Model(g); doc = g.json
names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in m.joints]
B0 = {jn[i]: np.linalg.inv(m.inverse_binds[i]) for i in range(len(jn))}
cols = json.load(open(CJ))
S3 = 'Bip01 Spine3'
for c in cols:
    heads = [B0[nm][:3, 3] for nm in c['names']]
    e = np.array(c['joints'][-1]); j0 = np.array(c['joints'][0])
    lift = heads[0] - np.array([j0[0], j0[2], -j0[1]])
    pts = np.array(heads + [np.array([e[0], e[2], -e[1]]) + lift])
    c['pts0'] = pts
    c['L'] = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    c['d0'] = np.diff(pts, axis=0) / c['L'][:, None]
    th = math.radians(c['th']); c['out0'] = np.array([math.sin(th), 0.0, -math.cos(th)])
NC = len(cols)
SS = np.linspace(0, 0.45, 46)


def outpush(Q, n, a, b, r):
    """least s >= 0 (per point) that puts Q + s n at r from the capsule axis ab: the cloth leaves a leg along its own outward direction
    (a radial push from a heel between two columns pried the columns apart instead of lifting the cloth)"""
    X = Q[:, None, :] + SS[None, :, None] * n[:, None, :] if n.ndim == 2 else Q[:, None, :] + SS[None, :, None] * n[None, None, :]
    ab = b - a; t = np.clip(((X - a) @ ab) / (ab @ ab), 0, 1)
    dist = np.linalg.norm(X - (a + t[..., None] * ab), axis=2)
    ok = dist >= r
    return np.where(ok.any(1), SS[np.argmax(ok, 1)], SS[-1])
order = sorted(range(NC), key=lambda k: cols[k]['th'])
PAIRS = []                                                   # (k, k', level, rest distance)
for a, b in zip(order[:-1], order[1:]):
    n = min(len(cols[a]['pts0']), len(cols[b]['pts0']))
    if (abs(cols[a]['th']) > 110) != (abs(cols[b]['th']) > 110): continue      # front mantle vs main cloak: different heights
    for j in range(1, n):
        PAIRS.append((a, b, j, float(np.linalg.norm(cols[a]['pts0'][j] - cols[b]['pts0'][j]))))
B = 'Bip01 '
CAPS = []
for S in 'LR':
    CAPS += [(B + S + ' Thigh', B + S + ' Calf', None, RAD['Thigh'], 'leg'), (B + S + ' Calf', B + S + ' Foot', None, RAD['Calf'], 'leg'),
             (B + S + ' Foot', B + S + ' Toe0', -0.35, 0.06, 'leg'),
             (B + S + ' UpperArm', B + S + ' Forearm', None, RAD['UpperArm'], 'arm'), (B + S + ' Forearm', B + S + ' Hand', None, RAD['Forearm'], 'arm'),
             (B + S + ' Hand', B + S + ' Finger1', 1.6, 0.045, 'arm')]
CAPS.append((B + 'Pelvis', B + 'Spine1', None, 0.135, 'hip'))


def frame_caps(W):
    out = []
    for a, b, ext, r, kind in CAPS:
        pa = W[ix[a]][:3, 3]; pb = W[ix[b]][:3, 3]
        if ext is not None and ext > 0: pb = pa + (pb - pa) * ext
        if ext is not None and ext < 0: pa = pa + (pa - pb) * (-ext)           # the heel behind the ankle
        out.append((pa, pb, r + MARGIN[kind]))
    return out


def closest(P, a, b):
    ab = b - a; t = np.clip((P - a) @ ab / (ab @ ab), 0, 1); return a + np.outer(t, ab)


caps0 = frame_caps(m.world({}))
for c in cols:                                                # bind-pose distance per joint / midpoint and capsule
    P = c['pts0']; M = 0.5 * (P[1:] + P[:-1])
    c['bindJ'] = np.array([np.linalg.norm(P - closest(P, a, b), axis=1) if CAPS[i][4] == 'arm' else np.full(len(P), 9.0) for i, (a, b, r) in enumerate(caps0)])
    c['bindM'] = np.array([np.linalg.norm(M - closest(M, a, b), axis=1) if CAPS[i][4] == 'arm' else np.full(len(M), 9.0) for i, (a, b, r) in enumerate(caps0)])


def axis_rot(ax, a):
    ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K


def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); s_ = np.linalg.norm(v)
    if s_ < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s_ ** 2)


def yaw_of(R):
    f = R @ np.array([0, 0, 1.0]); return math.atan2(f[0], f[2])


S0 = B0[S3]; R_S0 = S0[:3, :3]; yaw0 = yaw_of(R_S0)


def solve(W, clip, floor=None):
    floor = FLOOR if floor is None else floor
    S = W[ix[S3]]; Rr = S[:3, :3] @ R_S0.T
    up_t = Rr @ np.array([0, 1.0, 0]); tilt = math.degrees(math.acos(np.clip(up_t[1], -1, 1)))
    gfac = 1 - np.clip((tilt - 15) / 30, 0, 1)             # lying: the rest drape with the torso (a plumb drape bunches on the floor)
    Ry = axis_rot(np.array([0, 1.0, 0]), yaw_of(S[:3, :3]) - yaw0)
    side = Ry @ np.array([1.0, 0, 0]); trail = math.radians(TRAIL.get(clip, 0.0))
    caps = frame_caps(W)
    P = []
    for c in cols:
        p = [(S @ np.linalg.inv(S0) @ np.r_[c['pts0'][0], 1])[:3]]
        nseg = len(c['L'])
        for j in range(nseg):
            gj = GRAV[min(j, 3)] * gfac
            dr = Rr @ c['d0'][j]; dp = Ry @ c['d0'][j]
            if trail: dp = axis_rot(side, -trail * (0.4 + 0.6 * j / max(1, nseg - 1))) @ dp
            t = (1 - gj) * dr + gj * dp; t /= np.linalg.norm(t)
            p.append(p[-1] + t * c['L'][j])
        P.append(np.array(p))
    for it in range(ITER):
        for k, c in enumerate(cols):                         # collisions: joints and midpoints
            Pk = P[k]; nk = Rr @ c['out0']
            for ci, (a, b, r) in enumerate(caps):
                leg = CAPS[ci][4] != 'arm'
                rj = np.minimum(r, c['bindJ'][ci] - 0.003); rj[0] = 0
                if leg:
                    sj = outpush(Pk, nk, a, b, r); sj[0] = 0
                    Pk += np.outer(sj, nk)
                else:
                    q = closest(Pk, a, b); d = Pk - q; dn = np.linalg.norm(d, axis=1)
                    push = np.where(dn < rj, rj - dn, 0)
                    Pk += d / np.maximum(dn, 1e-6)[:, None] * push[:, None]
                rm = np.minimum(r, c['bindM'][ci] - 0.003)
                for f in (0.33, 0.5, 0.67):                  # points along each segment: the lower joint swings out by the lever
                    M = Pk[:-1] + (Pk[1:] - Pk[:-1]) * f
                    if leg:
                        Pk[1:] += np.outer(outpush(M, nk, a, b, r) / f, nk)
                    else:
                        q = closest(M, a, b); d = M - q; dn = np.linalg.norm(d, axis=1)
                        pm = np.where(dn < rm, rm - dn, 0) / f
                        Pk[1:] += d / np.maximum(dn, 1e-6)[:, None] * pm[:, None]
            Pk[:, 1] = np.maximum(Pk[:, 1], floor)
        PA_ = np.array([P[a][j] for a, b, j, d0 in PAIRS]); PA0 = np.array([P[a][j - 1] for a, b, j, d0 in PAIRS])
        PB_ = np.array([P[b][j] for a, b, j, d0 in PAIRS]); PB0 = np.array([P[b][j - 1] for a, b, j, d0 in PAIRS])
        mvA = np.zeros_like(PA_); mvB = np.zeros_like(PB_)
        NA = np.array([Rr @ cols[a]['out0'] for a, b, j, d0 in PAIRS]); NB = np.array([Rr @ cols[b]['out0'] for a, b, j, d0 in PAIRS])
        for ci, (ca, cb, r) in enumerate(caps):            # the cloth between two columns (a heel kicked back between them)
            if CAPS[ci][4] != 'leg': continue
            for v in (0.5, 1.0):
                pa_ = PA0 + (PA_ - PA0) * v; pb_ = PB0 + (PB_ - PB0) * v
                for u in (0.33, 0.67):
                    Q = pa_ + u * (pb_ - pa_); nq = NA * (1 - u) + NB * u; nq /= np.linalg.norm(nq, axis=1, keepdims=True)
                    sq = outpush(Q, nq, ca, cb, r) / v
                    mv = nq * sq[:, None]
                    mvA += mv * (1 - u) / ((1 - u) ** 2 + u ** 2); mvB += mv * u / ((1 - u) ** 2 + u ** 2)
        for i, (a, b, j, d0) in enumerate(PAIRS):
            P[a][j] += mvA[i]; P[b][j] += mvB[i]
        for a, b, j, d0 in PAIRS:                             # neighbouring columns
            v = P[b][j] - P[a][j]; d = np.linalg.norm(v)
            tgt = min(max(d, LAT_MIN * d0), LAT_MAX * d0)
            if abs(tgt - d) > 1e-6:
                corr = v / max(d, 1e-9) * (d - tgt) * 0.5
                P[a][j] += corr; P[b][j] -= corr
        for k, c in enumerate(cols):                          # lengths from the root
            Pk = P[k]
            for j in range(len(c['L'])):
                v = Pk[j + 1] - Pk[j]; Pk[j + 1] = Pk[j] + v / np.linalg.norm(v) * c['L'][j]
    return P


def rotations(W, P):
    S = W[ix[S3]]; Rr = S[:3, :3] @ R_S0.T
    world_R = {S3: S[:3, :3]}; out = {}
    for k, c in enumerate(cols):
        for j, nm in enumerate(c['names']):
            v = P[k][j + 1] - P[k][j]
            Rw = rot_between(Rr @ c['d0'][j], v) @ Rr @ B0[nm][:3, :3]
            par = S3 if j == 0 else c['names'][j - 1]
            out[nm] = matrix_quaternion(world_R[par].T @ Rw); world_R[nm] = Rw
    return out


# cloak and body vertices of the LOD0 body primitive (bind space = rest world): the corpse's floor pass
_pr = m.primitives[0]; _IBM = {jn[i]: m.inverse_binds[i] for i in range(len(jn))}
_dom = np.array([jn[j] for j in _pr['joints'][np.arange(len(_pr['joints'])), _pr['weights'].argmax(1)]])
_cv = np.nonzero(np.char.startswith(_dom.astype(str), 'Cloak'))[0]
_bv = np.nonzero(~np.char.startswith(_dom.astype(str), 'Cloak'))[0][::3]
_col_of = {nm: k for k, c in enumerate(cols) for nm in c['names']}
_cv_col = np.array([_col_of[d] for d in _dom[_cv]])


def skin(idx, mats):
    J = _pr['joints'][idx]; Wt = _pr['weights'][idx]; X = np.c_[_pr['positions'][idx], np.ones(len(idx))]
    out = np.zeros((len(idx), 3))
    for kk in range(J.shape[1]):
        M = np.array([mats[jn[j]] for j in J[:, kk]])
        out += Wt[:, kk:kk + 1] * np.einsum('vij,vj->vi', M, X)[:, :3]
    return out


def floor_pass(W, P, rounds=14, slack=0.003):
    """lying: no cloak vertex lower than the body's own lowest point (the corpse is then put on the floor by floor_fix --ground-death,
    with the cloak under it instead of 10-18 cm below it): columns whose vertices go lower are raised (joints up, lengths restored)"""
    mats = {n: W[ix[n]] @ _IBM[n] for n in jn}
    body_low = skin(_bv, mats)[:, 1].min()
    floor_eff = min(0.0, body_low) - slack
    for _ in range(rounds):
        S = W[ix[S3]]; Rr = S[:3, :3] @ R_S0.T
        for k, c in enumerate(cols):
            for j, nm in enumerate(c['names']):
                v = P[k][j + 1] - P[k][j]
                Rw = rot_between(Rr @ c['d0'][j], v) @ Rr @ B0[nm][:3, :3]
                M = np.eye(4); M[:3, :3] = Rw; M[:3, 3] = P[k][j]
                mats[nm] = M @ _IBM[nm]
        Y = skin(_cv, mats)[:, 1]
        moved = False
        for k, c in enumerate(cols):
            sel = _cv_col == k
            if not sel.any(): continue
            low = Y[sel].min()
            if low < floor_eff - 0.002:
                P[k][1:, 1] += 1.3 * (floor_eff - low) * np.linspace(0.6, 1.0, len(P[k]) - 1)
                for j in range(len(c['L'])):
                    vv = P[k][j + 1] - P[k][j]; P[k][j + 1] = P[k][j] + vv / np.linalg.norm(vv) * c['L'][j]
                moved = True
        if not moved: break
    return P


def lateral(P):
    r = [np.linalg.norm(P[b][j] - P[a][j]) / d0 for a, b, j, d0 in PAIRS]
    k = int(np.argmin(r)); a, b, j, d0 = PAIRS[k]
    return max(r), min(r), (cols[a]['th'], cols[b]['th'], j)


rep = {}; solved = {}
for an in doc['animations']:
    clip = an['name']
    if clip == 'Dead' or (ONLY and clip not in ONLY): continue
    T = np.array(sorted(m.clip_times(clip))); n = len(T); dt = (T[-1] - T[0]) / max(1, n - 1); loop = clip in LOOPS
    Ws = [m.world(m.sample(clip, float(t))) for t in T]
    # Death: while falling the hem may pass under the floor (a clamp there bunched the cloth, 14 % squashed); from the landing (LAND x the
    # clip) the floor holds again and the corpse's floor pass lays the cloak under the body
    land = T[-1] * LAND
    def _ramp(t):
        x = np.clip((t - land) / (0.3 * T[-1]), 0, 1); return x * x * (3 - 2 * x)
    Ps = [solve(W, clip, floor=(FALLFLOOR + (FLOOR - FALLFLOOR) * _ramp(t) if clip == 'Death' else None)) for W, t in zip(Ws, T)]
    loc = []
    for W, P in zip(Ws, Ps):
        Si = np.linalg.inv(W[ix[S3]])
        loc.append([(Si @ np.c_[Pk, np.ones(len(Pk))].T).T[:, :3] for Pk in P])
    for k in range(NC):
        arr = gaussian_filter1d(np.array([l[k] for l in loc]), SIGMA_T / dt, axis=0, mode='wrap' if loop else 'nearest')
        for f in range(n): loc[f][k] = arr[f]
    Ps = []
    for f_, (W, l) in enumerate(zip(Ws, loc)):
        S = W[ix[S3]]; P = []
        for k, c in enumerate(cols):
            Pk = (S @ np.c_[l[k], np.ones(len(l[k]))].T).T[:, :3]
            for j in range(len(c['L'])):
                v = Pk[j + 1] - Pk[j]; Pk[j + 1] = Pk[j] + v / np.linalg.norm(v) * c['L'][j]
            P.append(Pk)
        if clip == 'Death':                          # falling: the cloak at most 6 cm under the body's lowest point; landed: under the body
            P = floor_pass(W, P, slack=FALLSLACK + (0.003 - FALLSLACK) * _ramp(T[f_]))
        Ps.append(P)
    solved[clip] = (T, Ws, Ps)
    pen = []
    for W, P in zip(Ws, Ps):
        caps = frame_caps(W); worst = 0.0
        for ci, (ca, cb, r) in enumerate(caps):
            if CAPS[ci][4] != 'leg': continue
            for a, b, j, d0 in PAIRS:
                for v in (0.25, 0.5, 0.75, 1.0):
                    pa_ = P[a][j - 1] + (P[a][j] - P[a][j - 1]) * v; pb_ = P[b][j - 1] + (P[b][j] - P[b][j - 1]) * v
                    Q = pa_[None] + np.linspace(0, 1, 5)[:, None] * (pb_ - pa_)[None]
                    worst = min(worst, float((np.linalg.norm(Q - closest(Q, ca, cb), axis=1) - (r - MARGIN['leg'])).min()))
        pen.append(worst)
    lat = [lateral(P) for P in Ps]
    fm = int(np.argmin([x[1] for x in lat]))
    rep[clip] = {'leg_pen_cm': round(-100 * min(pen), 1), 'pen_frames': int(sum(x < -0.01 for x in pen)), 'lateral_max': round(float(max(x[0] for x in lat)), 3), 'lateral_min': round(float(lat[fm][1]), 3), 'min_at': [round(float(T[fm]), 2), lat[fm][2]]}
    print(clip, rep[clip], flush=True)
T = np.array(sorted(m.clip_times('Dead')))
Ws = [m.world(m.sample('Dead', float(t))) for t in T]
Wl = solved['Death'][1][-1]; Pl = solved['Death'][2][-1]; Si = np.linalg.inv(Wl[ix[S3]])
solved['Dead'] = (T, Ws, [[(W[ix[S3]] @ Si @ np.c_[Pk, np.ones(len(Pk))].T).T[:, :3] for Pk in Pl] for W in Ws])
cn = [nm for c in cols for nm in c['names']]; cidx = {nm: ix[nm] for nm in cn}
for clip, (T, Ws, Ps) in solved.items():
    Q = {nm: [] for nm in cn}
    for W, P in zip(Ws, Ps):
        lq = rotations(W, P)
        for nm in cn: Q[nm].append(lq[nm])
    an = next(a for a in doc['animations'] if a['name'] == clip)
    an['channels'] = [c for c in an['channels'] if not (c['target']['node'] in cidx.values() and c['target']['path'] == 'rotation')]
    tacc = g.append_accessor(T.astype(np.float32), 'SCALAR')
    doc['accessors'][tacc]['min'] = [float(T.min())]; doc['accessors'][tacc]['max'] = [float(T.max())]
    for nm in cn:
        q = np.array(Q[nm])
        for k in range(1, len(q)):
            if q[k] @ q[k - 1] < 0: q[k] = -q[k]
        qa = g.append_accessor(q.astype(np.float32), 'VEC4')
        an['samplers'].append(dict(input=tacc, output=qa, interpolation='LINEAR'))
        an['channels'].append(dict(sampler=len(an['samplers']) - 1, target=dict(node=cidx[nm], path='rotation')))
g.write(Path(OUT))
json.dump(rep, open(REP, 'w'), indent=1)
print('CLOAK keyed', OUT)
