#!/usr/bin/env python3
"""Coat sectors (XCoat*1-2) and the tabard chain (XPanelF1-4), all under Bip01 Spine (the thighs' parent), keyed per clip on its own keys.
In the Spine's bind frame each chain hangs in its radial plane (the tabard at the front, a coat sector at its azimuth). Per key, link by link from the
top: the least outward swing beyond the bind's own angle that keeps every leg, boot and knee point of the chain's sector MARGIN inside the cloth
(closed form on the points: atan of out + MARGIN over down, points at least 4 cm below the hinge; a margin arcsine blew up on the crotch right under the tabard's hinge). Gravity: each link's base is its bind angle turned to the world's down, and no link above horizontal in the world (the angle nearest the needed one
among those that hang). Floor: no link tip under FLOOR (run after floor.sh, so the world floor is y = 0). Curves: running maximum (HOLD) and Gaussian
(SIGMA) on the clip's keys, circular on loops, never per frame. Args: <in glb> <out glb> <rig json> <asm npz> <report json>"""
import json, sys, os
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, 'scripts')
from glb_pose import Glb, Model, matrix_quaternion
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
from rig_bones import PANELS, panel_bones, COAT, COAT_Z, coat_bones
IN, OUT, RIG, NPZ, REP = sys.argv[1:6]
MARGIN, HOLD, SIGMA = 0.015, 0.12, 0.04; MAXBEND = np.radians(float(os.environ.get("MAXBEND", "70"))); INWARD = np.radians(float(os.environ.get("INWARD", "0"))); NEIGH = np.radians(float(os.environ.get("NEIGH", "30"))); UPSIDE = int(os.environ.get("UPSIDE", "1"))
MAXA = np.radians(150); FLOOR = 0.015; THIGH_PAD = np.radians(6); LIE_HOLD = float(os.environ.get('LIE_HOLD', '1')); LIE_CAP = np.radians(float(os.environ.get('LIE_CAP', '60'))); FLARE_RELAX = float(os.environ.get('FLARE_RELAX', '0.8')); LIE_LEGS = float(os.environ.get('LIE_LEGS', '1')); LIE_T0 = float(os.environ.get('LIE_T0', '35')); LIE_TW = float(os.environ.get('LIE_TW', '20')); LIE_IN = np.radians(float(os.environ.get('LIE_IN', '25')))      # lying base aims inside the leg line; the leg and hip points hold it on them      # lying: the bind's shape along the body (pure gravity without a body solve flipped the coat through the body, r9 test), swing capped
import os
DEBUG = os.environ.get('DEBUG', '').split(',') if os.environ.get('DEBUG') else []
DEBUG_CH = os.environ.get('DEBUG_CH', 'F,SFR,SFL').split(',')
LOOPS = ('Standing', 'Walking', 'Running', 'Backpedal', 'BackpedalRun')
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in m.joints]; ibm = {n: m.inverse_binds[i] for i, n in enumerate(jn)}
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def add(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g.accessors) - 1
def gl(p): return np.array([p[0], p[2], -p[1]], float)
R = json.load(open(RIG)); A = np.load(NPZ); aco, acomp = A['co'], A['comp']; an_ = [str(x) for x in A['names']]
SP = 'Bip01 Spine'; isp = ix[SP]; Ib = ibm[SP]; Rb = np.linalg.inv(Ib)[:3, :3]
UP = np.array([0, 1.0, 0])
# chains: bones, hinge points (glTF bind), outward unit (glTF), half width, tip below the last hinge
chains = {}
for k, az in COAT.items():
    r = np.array([np.sin(np.radians(az)), 0.0, -np.cos(np.radians(az))])
    H = [gl(p) for p in R['coat'][k]]
    cv = aco[(acomp == an_.index('torso')) & (aco[:, 2] < COAT_Z[1])]
    azv = np.degrees(np.arctan2(cv[:, 0], cv[:, 1])); sel = np.abs(((azv - az) + 180) % 360 - 180) < 20
    hem = float(cv[sel, 2].min()) if sel.any() else 0.1
    chains[k] = dict(bones=coat_bones(k), H=H, r=r, half=0.15, tip=H[-1] + (hem - COAT_Z[1]) * np.array([0, 1.0, 0]), thighs=['L', 'R'] if k in ('SFR', 'SFL') else [], sides=['R'] if az > 20 else (['L'] if az < -20 else ['L', 'R']))
tv = aco[acomp == an_.index('tabard')]
chains['F'] = dict(bones=panel_bones('F'), H=[gl([0.0, R['panel_y']['F'], z]) for z in PANELS['F']], r=np.array([0, 0, 1.0]), half=float(np.abs(tv[:, 0]).max()) + 0.015,
                   tip=gl([0.0, R['panel_y']['F'], float(tv[:, 2].min())]), thighs=['L', 'R'])
pr = m.primitives
J = np.vstack([p['joints'] for p in pr]); W_ = np.vstack([p['weights'] for p in pr])
legb = [i for i, n in enumerate(jn) if any(k in n for k in ('Thigh', 'Calf', 'Foot'))]
P_b = np.vstack([np.asarray(p['positions'], float) for p in pr])
ob_v = np.where(((np.isin(J, legb) * W_).sum(1) > 0.45) & (P_b[:, 1] < 0.85))[0]
hipb = [i for i, n in enumerate(jn) if n in ('Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1') or 'Thigh' in n]
clothb = [i for i, n in enumerate(jn) if n.startswith('XCoat') or n.startswith('XPanel')]
hip_v = np.where(((np.isin(J, hipb) * W_).sum(1) > 0.9) & ((np.isin(J, clothb) * W_).sum(1) < 0.05) & (P_b[:, 1] < 0.85) & (P_b[:, 1] > 0.55))[0]
ob_v = np.union1d(ob_v, hip_v)          # r9: the hips and seat under the coat are obstacles too (a lying corpse's coat rests on them)       # r9: not the trouser top under the belt (inside the torso, it rode above the tabard's hinge)
def skinned(w): return np.vstack([r_[0] for r_ in m.skinned_positions(w)])
print('obstacle verts', len(ob_v))
def rot(axis, th):
    axis = axis / np.linalg.norm(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K
report = {}
for an in g.animations:
    ch = next(c for c in an.channels if names[c.target.node] == SP)
    a = g.accessors[an.samplers[ch.sampler].input]; bv = g.bufferViews[a.bufferView]; o = (bv.byteOffset or 0) + (a.byteOffset or 0)
    ts = np.frombuffer(bytes(blob[o:o + 4 * a.count]), 'f4').copy(); tin = an.samplers[ch.sampler].input
    n = len(ts); loop = an.name in LOOPS; dt = np.median(np.diff(ts)) if n > 1 else 1 / 30
    wbs = [m.world(m.sample(an.name, float(t))) for t in ts]
    Ps = [skinned(w)[ob_v] for w in wbs]
    Ps0 = skinned(m.world({}))[ob_v]
    res = {}; SOLVED = {}
    for ck, C in chains.items():
        H = C['H'] + [C['tip']]; r = C['r']; t_ax = np.cross(UP, r); nl = len(C['bones'])
        Ls = [np.linalg.norm(H[i + 1] - H[i]) for i in range(nl)]
        a0 = []                                      # bind angles from straight down, outward positive (cumulative)
        for i in range(nl):
            d = H[i + 1] - H[i]; a0.append(np.arctan2(d @ r, -(d @ UP)))
        need = np.zeros((n, nl)); TH_DBG = {}; LIE = np.zeros(n)
        def requirement(Q, angles=None):
            # per link: the swing the obstacle points ask for (-inf when none), chained on the given angles (or on the asked ones)
            q = Q[np.abs((Q - H[0]) @ t_ax) < C['half']]; cur = H[0].copy(); req = []; used = []
            for i in range(nl):
                d = q - cur; down = -(d @ UP); out = d @ r; dist = np.hypot(down, out)
                sel = (dist > 0.05) & (out > -0.02) & (dist < Ls[i] + 0.15)    # r9: any leg point ahead of the hinge, also above it (a knee raised over the belt in Running)    # r6: a thigh raised to the hinge's height counts (Running)
                rq = float(((np.arctan2(out[sel], down[sel]) + np.arcsin(np.minimum(MARGIN / dist[sel], 1.0)))).max()) if sel.any() else -9.0
                req.append(rq); ai = angles[i] if angles is not None else None
                used.append(ai); cur = cur + Ls[i] * (-np.cos(ai) * UP + np.sin(ai) * r) if ai is not None else cur
            return req
        Qb = (np.linalg.inv(m.world({})[isp] @ Ib) @ np.c_[Ps0, np.ones(len(Ps0))].T).T[:, :3]
        req_b = requirement(Qb, a0); slack = [max(a0[i], req_b[i]) for i in range(nl)]
        for f, w in enumerate(wbs):
            Sp = w[isp] @ Ib; Rp = Sp[:3, :3]
            Q = (np.linalg.inv(Sp) @ np.c_[Ps[f], np.ones(len(Ps[f]))].T).T[:, :3]      # obstacles in the Spine's bind frame
            q = Q[np.abs((Q - H[0]) @ t_ax) < C['half']]
            cur = H[0].copy(); prev = None; ang = np.zeros(nl); extra_prev = 0.0
            # r9 thigh rule (Running): links whose hinge lies along a thigh in front of this chain take at least that thigh's angle in the
            # chain's plane (+ THIGH_PAD), so the cloth rides the raised thigh instead of letting it through between the links' blends
            th_need = []
            TH_DBG[f] = th_need
            # r9 lying: the cloth lies along the legs (thigh line for the upper links, shin line for the lower ones) in this chain's plane
            leg_ang = {}
            for sd in ('L', 'R'):
                pts_ = [(np.linalg.inv(Sp) @ np.r_[w[ix[f'Bip01 {sd} {b_}']][:3, 3], 1])[:3] for b_ in ('Thigh', 'Calf', 'Foot')]
                leg_ang[sd] = [float(np.arctan2((pts_[k + 1] - pts_[k]) @ r, -((pts_[k + 1] - pts_[k]) @ UP))) for k in (0, 1)]
            sides_ = C.get('sides', ['L', 'R'])
            lie_line = [float(np.mean([leg_ang[sd][0 if i < max(1, nl // 2) else 1] for sd in sides_])) for i in range(nl)]
            for sd in C['thighs']:
                hp = (np.linalg.inv(Sp) @ np.r_[w[ix[f'Bip01 {sd} Thigh']][:3, 3], 1])[:3]; kp = (np.linalg.inv(Sp) @ np.r_[w[ix[f'Bip01 {sd} Calf']][:3, 3], 1])[:3]
                dv = kp - hp; th_need.append((float(np.arctan2(dv @ r, -(dv @ UP))), float(np.linalg.norm(dv))))
            for i in range(nl):
                d = q - cur; down = -(d @ UP); out = d @ r; dist = np.hypot(down, out)
                sel = (dist > 0.05) & (out > -0.02) & (dist < Ls[i] + 0.15)    # r9: any leg point ahead of the hinge, also above it (a knee raised over the belt in Running)    # r6: a thigh raised to the hinge's height counts (Running)
                gb = Rp.T @ np.array([0, -1.0, 0]); gam = float(np.arctan2(gb @ r, -(gb @ UP)))
                tilt = float(np.degrees(np.arccos(np.clip(-(gb @ UP), -1, 1))))           # 0 upright, 90 lying
                up_side = float(np.clip((Rp @ r)[1] / 0.5, 0, 1)) if UPSIDE else 1.0   # r12: only a sector facing up is laid in onto the legs; one under the body keeps the legs' line
                lie = float(np.clip((tilt - LIE_T0) / LIE_TW, 0, 1)); lie = lie * lie * (3 - 2 * lie); lie_raw = lie; lie = lie * LIE_HOLD
                ai = (a0[i] * (1 - FLARE_RELAX * lie) + gam * (1 - lie)) * (1 - lie_raw * LIE_LEGS) + (lie_line[i] - LIE_IN * up_side) * lie_raw * LIE_LEGS               # r9: lying relaxes the A-line flare towards the legs; base: the bind's shape turned to hang along the world's down (cloth drapes below the knee);
                                                           # lying (r4, Dead2 face down): the bind's own shape, the coat lies along the body
                # gravity: the base must not point above horizontal in the world (r9: on the base only; a leg may push the cloth higher)
                if lie < 0.5 and (Rp @ (-np.cos(ai) * UP + np.sin(ai) * r))[1] > 0.05:
                    cand = np.radians(np.arange(-110, 111, 2.5))
                    dirs = np.array([Rp @ (-np.cos(c_) * UP + np.sin(c_) * r) for c_ in cand])
                    ok = cand[dirs[:, 1] <= 0.05]
                    if len(ok): ai = float(ok[np.argmin(np.abs(ok - ai))])
                if lie_raw < 0.5: ai = max(ai, a0[i] - INWARD)   # r12: upright, no link swings more than INWARD inside its bind angle (the back coat
                                                                 # hung in by gravity folded its own lining: strip collapse in Fidget, Running)
                along_ = sum(Ls[:i])
                for th_a, th_l in th_need:
                    if along_ < th_l * 0.85 and th_a > 0.3: ai = max(ai, th_a + THIGH_PAD)
                if sel.any():
                    req = float(((np.arctan2(out[sel], down[sel]) + np.arcsin(np.minimum(MARGIN / dist[sel], 1.0)))).max())
                    ai = max(ai, a0[i] + ((req - slack[i]) if lie_raw > 0.5 else max(0.0, req - slack[i])))      # r9: lying, the bind's clearance is the reference both ways (the coat may come in onto the legs); upright never inside the bind's shape (r10 folded the back coat in Fidget)
                if prev is not None: ai = float(np.clip(ai, prev - MAXBEND, prev + MAXBEND))
                ai = float(np.clip(ai, -MAXA, MAXA)); ang[i] = ai; prev = ai; extra_prev = ai - a0[i]
                cur = cur + Ls[i] * (-np.cos(ai) * UP + np.sin(ai) * r)
            need[f] = ang; LIE[f] = lie_raw
        Aa = need.copy(); mode = 'wrap' if loop else 'nearest'
        for i in range(nl):
            Aa[:, i] = maximum_filter1d(Aa[:, i], max(1, int(round(HOLD / dt)) | 1), mode=mode)
            Aa[:, i] = gaussian_filter1d(Aa[:, i], SIGMA / dt, mode=mode)
        # floor
        for f, w in enumerate(wbs):
            Sp = w[isp] @ Ib; cur = H[0].copy()
            for i in range(nl):
                for _ in range(16):
                    tip = cur + Ls[i] * (-np.cos(Aa[f, i]) * UP + np.sin(Aa[f, i]) * r)
                    wy = (Sp @ np.r_[tip, 1])[1]
                    if wy >= FLOOR: break
                    t2 = cur + Ls[i] * (-np.cos(Aa[f, i] + 0.05) * UP + np.sin(Aa[f, i] + 0.05) * r)
                    Aa[f, i] += 0.08 if (Sp @ np.r_[t2, 1])[1] > wy else -0.08
                cur = cur + Ls[i] * (-np.cos(Aa[f, i]) * UP + np.sin(Aa[f, i]) * r)
        for i in range(nl): Aa[:, i] = gaussian_filter1d(Aa[:, i], SIGMA / dt, mode=mode)
        # lying: the swing away from the bind's shape is capped (the floor clamp could turn a front panel pinned under a face-down corpse up
        # through 167 deg into a wing)
        for f in range(n):
            if LIE[f] > 0.01:
                cap = np.radians(100) * (1 - LIE[f]) + LIE_CAP * LIE[f]
                Aa[f] = np.clip(Aa[f], np.array(a0) - cap, np.array(a0) + cap)
        if DEBUG and an.name in DEBUG and ck in DEBUG_CH:
            for f, w in enumerate(wbs):
                Sp = w[isp] @ Ib; Q = (np.linalg.inv(Sp) @ np.c_[Ps[f], np.ones(len(Ps[f]))].T).T[:, :3]
                q = Q[np.abs((Q - H[0]) @ t_ax) < C['half']]; cur = H[0].copy(); viol = []
                for i in range(nl):
                    dvec = -np.cos(Aa[f, i]) * UP + np.sin(Aa[f, i]) * r; d = q - cur; along = d @ dvec; outn = d @ (np.sin(Aa[f, i]) * UP + np.cos(Aa[f, i]) * r)
                    m_ = (along > 0) & (along < Ls[i]); viol.append(round(float(outn[m_].max()) * 100, 1) if m_.any() else None); cur = cur + Ls[i] * dvec
                print('DBG', an.name, ck, f, 'thigh', [round(float(np.degrees(a_)), 0) for a_, l_ in TH_DBG.get(f, [])], 'need', np.degrees(need[f]).round(0).tolist(), 'final', np.degrees(Aa[f]).round(0).tolist(), 'max out of line cm', viol)
        SOLVED[ck] = (Aa, np.array(a0), LIE.copy())
    # r12 neighbours: upright, a coat sector's link may not stand more than NEIGH above its neighbours' (a heel kicked into the back
    # coat lifted B2 76 deg past BL2 in Running and sheared the faces between them); the lower neighbour is raised (outward only)
    ring = [k for k in os.environ.get('NEIGH_RING', 'BR,B,BL').split(',') if k in SOLVED]   # the back sectors (the heel's kick); the sides took folds of their own
    for _ in range(len(ring)):
        for j, k in enumerate(ring):
            Ak, ak, Lk = SOLVED[k]
            for jn_ in (j - 1, j + 1):
                if 0 <= jn_ < len(ring):
                    An, an0, _ = SOLVED[ring[jn_]]
                    up_ = (Lk < 0.5)[:, None]
                    Ak[:] = np.where(up_, np.maximum(Ak - ak[None], (An - an0[None]) - NEIGH) + ak[None], Ak)
    for ck, C in chains.items():
        Aa, a0, _ = SOLVED[ck]; n = len(Aa); nl = len(C['bones'])
        delta = Aa - np.array(a0)[None]
        res[ck] = round(float(np.degrees(np.abs(delta).max())), 1)
        an.channels = [c for c in an.channels if names[c.target.node] not in C['bones']]
        t_ax = np.cross(UP, C['r'])
        for i, b in enumerate(C['bones']):
            rel = delta[:, i] - (delta[:, i - 1] if i else 0.0)
            Qk = np.array([matrix_quaternion(Rb.T @ rot(t_ax, -x_) @ Rb) for x_ in rel])
            for f in range(1, n):
                if Qk[f] @ Qk[f - 1] < 0: Qk[f] *= -1
            s = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(Qk, 'VEC4'), interpolation='LINEAR'))
            an.channels.append(AnimationChannel(sampler=s, target=AnimationChannelTarget(node=ix[b], path='rotation')))
    report[an.name] = res
    print('COAT', an.name, res, flush=True)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
json.dump(report, open(REP, 'w'), indent=0)
