"""Salamander arm and spear motion re-authored after the MM8 Raven Man (m584): the polearm frame, the two hand
contacts and the elbow directions follow the Raven Man's clips in chest space (read_spear.py -> work/raven_spear.json),
scaled by arm length onto the Salamander's shoulders; the serpent body, tail, head, finger grips, the Fidget left-hand
release and the Death release/settle are those of ../../../mm8_m568_claude/scripts/animate_salamander.py.
Opens the editable master (mm8_m568_claude/export/mm8_m568.blend, read only), rebuilds the nine actions and saves
work/spear_master.blend. SPEAR_MODE=original reproduces the installed motion (pipeline check).
Env: SPEAR_SR / SPEAR_SL = shaft parameters of the right / left hand contacts (polearm local, metres from the centre)."""
import bpy, json, math, os
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
P = Path(__file__).resolve().parents[2]; SRC = P.parent / 'mm8_m568_claude'
bpy.ops.wm.open_mainfile(filepath=str(SRC / 'export/mm8_m568.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; weapon = bpy.data.objects['PolearmMesh']; sc = bpy.context.scene
D = json.loads((SRC / 'work/rig.json').read_text()); G = json.loads((SRC / 'work/grip_pose.json').read_text())
B = D['bones']; J0 = np.array(D['tail']['joints']); K = D['tail']['root_index']; L = np.linalg.norm(np.diff(J0, axis=0), axis=1)
R = {n: rig.data.bones[n].matrix_local.copy() for n in B}; REL = {n: R[b['parent']].inverted() @ R[n] if b['parent'] else R[n] for n, b in B.items()}
FPS = 48; sc.render.fps = FPS
DUR = {'Standing': 3., 'Walk': 1., 'Running': .75, 'Fidget': .625, 'Attack': 4 / 3, 'Cast': 1.25, 'Hit': .625, 'Death': .75, 'Dead': 1.}
MODE = os.environ.get('SPEAR_MODE', 'raven')
CAST_TR = float(os.environ.get('SPEAR_CAST_TR', '.15'))  # Raven Attack time of the Cast release pose (rising lift)
S_R = float(os.environ.get('SPEAR_SR', '-0.15')); S_L = float(os.environ.get('SPEAR_SL', '-0.45'))
if MODE == 'original':
    S_R, S_L = .25, -.25


def norm(v): return v / max(np.linalg.norm(v), 1e-9)
def ss(x): x = np.clip(x, 0, 1); return float(x * x * (3 - 2 * x))
def env(t, a, b, c): return ss((t - a) / (b - a)) * (1 - ss((t - b) / (c - b)))
def mat(rot, p): m = rot.to_4x4(); m.translation = Vector(p); return m


def frame(a, n):
    a = norm(np.array(a)); n = norm(np.array(n) - a * np.dot(n, a)); return Matrix(np.column_stack([a, n, np.cross(a, n)]))


# Raven Man spear handling, mapped into the Salamander's chest rest space: p_s = c_s + k (p_r - c_r), c = shoulder
# midpoint, k = arm length ratio (upper arm + forearm, rest).
RV = json.loads((P / 'work/raven_spear.json').read_text())
def arm_len(rest, sd): return np.linalg.norm(np.subtract(rest[f'B_{sd}_Forearm'], rest[f'B_{sd}_UpperArm'])) + np.linalg.norm(np.subtract(rest[f'B_{sd}_Hand'], rest[f'B_{sd}_Forearm']))
SAL = {n: B[n]['head'] for n in ['B_L_UpperArm', 'B_R_UpperArm', 'B_L_Forearm', 'B_R_Forearm', 'B_L_Hand', 'B_R_Hand']}
C_R = (np.array(RV['rest']['B_L_UpperArm']) + RV['rest']['B_R_UpperArm']) / 2; C_S = (np.array(SAL['B_L_UpperArm']) + SAL['B_R_UpperArm']) / 2
KS = (arm_len(SAL, 'L') + arm_len(SAL, 'R')) / (arm_len(RV['rest'], 'L') + arm_len(RV['rest'], 'R'))
def mp(p): return C_S + KS * (np.array(p) - C_R)


def raven(clip, tr):
    fr = RV['clips'][clip]['frames']; ts = np.array([f['t'] for f in fr]); tr = float(np.clip(tr, ts[0], ts[-1]))
    k = min(int(np.searchsorted(ts, tr, 'right') - 1), len(fr) - 2); f = (tr - ts[k]) / max(ts[k + 1] - ts[k], 1e-9)
    def lerp(key):
        return (1 - f) * np.array(fr[k][key], float) + f * np.array(fr[k + 1][key], float)
    o, ax, side = lerp('origin'), norm(lerp('axis')), lerp('side')
    sr, sl = (1 - f) * fr[k]['R_s'] + f * fr[k + 1]['R_s'], (1 - f) * fr[k]['L_s'] + f * fr[k + 1]['L_s']
    mid = o + ax * (sr + sl) / 2
    wdir = {}
    for sd, s_ in (('L', sl), ('R', sr)):  # where each wrist sits around the shaft (perpendicular to it)
        w = lerp(f'{sd}_wrist') - (o + ax * s_); wdir[sd] = norm(w - ax * np.dot(w, ax))
    return {'mid': mp(mid), 'axis': ax, 'side': norm(side - ax * np.dot(side, ax)), 'L_elbow': mp(lerp('L_elbow')),
            'R_elbow': mp(lerp('R_elbow')), 'L_wdir': wdir['L'], 'R_wdir': wdir['R'],
            'L_shoulder': mp(lerp('L_shoulder')), 'R_shoulder': mp(lerp('R_shoulder'))}


def blend(a, b, w):
    out = {k: (1 - w) * a[k] + w * b[k] for k in a}
    out['axis'] = norm(out['axis']); out['L_wdir'] = norm(out['L_wdir']); out['R_wdir'] = norm(out['R_wdir']); out['side'] = norm(out['side'] - out['axis'] * np.dot(out['side'], out['axis']))
    return out


def held(role, t):
    """Raven Man state, with any end-to-start drift of the source spread linearly over the clip (loops close; one-shot
    clips end in their own start pose)."""
    if role in ('Death', 'Dead'):
        return held_raw(role, t)
    a, b = held_raw(role, 0.), held_raw(role, DUR[role]); w = t / DUR[role]
    out = {k: v + w * (a[k] - b[k]) for k, v in held_raw(role, t).items()}
    for k in ('axis', 'L_wdir', 'R_wdir'):
        out[k] = norm(out[k])
    out['side'] = norm(out['side'] - out['axis'] * np.dot(out['side'], out['axis']))
    return out


def held_raw(role, t):
    """Raven Man state for a Salamander role and time (clip time warps keep the Salamander's durations and contacts)."""
    if role == 'Standing':
        return raven('Standing', t * 2 / 3)
    if role in ('Walk', 'Running'):
        return raven('Walking', t / DUR[role])
    if role == 'Fidget':
        return raven('Standing', t * 2 / 3)
    if role == 'Attack':  # Raven impact 26/30 s -> Salamander impact 1.0 s; end 35/30 s -> 4/3 s
        tr = t * (26 / 30) if t <= 1 else 26 / 30 + (t - 1) / (1 / 3) * (9 / 30)
        return raven('Attack', tr)
    if role == 'Cast':  # rise into the Raven Man's attack lift for the 1.0 s release, then settle back to the guard
        if t <= 1:
            return raven('Attack', CAST_TR * ss(t / 1.))
        return blend(raven('Attack', CAST_TR), raven('Standing', 0), ss((t - 1) / .25))
    if role == 'Hit':
        return raven('Hit', t * (11 / 15) / .625)
    if role in ('Death', 'Dead'):
        return raven('Death', min(t, .24) * (1 / 3) / .24)
    raise KeyError(role)


# wrist -> middle knuckle in hand space and its rest angle to the forearm (wrist bend = change of this angle)
KNUCKLE = {sd: R[f'B_{sd}_Hand'].to_3x3().transposed() @ (R[f'B_{sd}_Finger2'].translation - R[f'B_{sd}_Hand'].translation) for sd in 'LR'}
REST_BEND = {sd: math.degrees((R[f'B_{sd}_Finger2'].translation - R[f'B_{sd}_Hand'].translation).angle(R[f'B_{sd}_Hand'].translation - R[f'B_{sd}_Forearm'].translation)) for sd in 'LR'}
PREV = {}
C0 = np.array([-.04, -.35, 1.38]); A0 = norm(np.array([-.83, -.12, .545]))
# Front of the torso in rest space (chest space): the most forward body point within 22 cm of the centreline per
# 5 cm of height, from vertices that are not arm-weighted. The Raven Man is slimmer; hands are kept in front of it.
_names = {g.index: g.name for g in body.vertex_groups}
_armish = lambda v: sum(g.weight for g in v.groups if any(k in _names[g.group] for k in ('Arm', 'Hand', 'Finger', 'Clavicle'))) > .2
_rest = np.array([v.co[:] for v in body.data.vertices if not _armish(v)])
FRONT_Z = np.arange(.80, 2.05, .05)
FRONT_Y = np.array([(_rest[(np.abs(_rest[:, 0]) < .22) & (np.abs(_rest[:, 2] - z) < .04), 1].min()
                     if ((np.abs(_rest[:, 0]) < .22) & (np.abs(_rest[:, 2] - z) < .04)).any() else 0.) for z in FRONT_Z])
def front_y(z): return float(np.interp(z, FRONT_Z, FRONT_Y))


def pose(role, t):
    if role == 'Dead':
        role, t = 'Death', DUR['Death']
    phase = 2 * math.pi * t / DUR[role]; gait = role in ['Walk', 'Running']; fall = ss((t - .15) / .53) if role == 'Death' else 0.
    hit = env(t, 0, .17, .625) if role == 'Hit' else env(t, 0, .11, .28) * .55 if role == 'Death' else 0.
    wind = env(t, 0, .40, .78) if role == 'Attack' else 0.; strike = env(t, .48, 1., 4 / 3) if role == 'Attack' else 0.
    cast = env(t, 0, 1., 1.25) if role == 'Cast' else 0.; fidget = env(t, 0, .31, .625) if role == 'Fidget' else 0.
    pitch = .012 * math.sin(phase) if role == 'Standing' else -.20 * hit - .13 * wind - .15 * strike
    wave = (.52 if role == 'Running' else .38) if gait else .025
    pts = J0.copy()
    for i in list(range(K - 1, -1, -1)) + list(range(K, len(L))):
        up = i < K; d = Vector(J0[i] - J0[i + 1] if up else J0[i + 1] - J0[i]); d.normalize(); u = (K - i) / K if up else (i - K) / (len(L) - K)
        if up:
            yaw = (.045 * math.sin(phase - u * 3) if gait else 0) + fall * 1.15 * u
            d = Matrix.Rotation(yaw, 3, 'Y') @ Matrix.Rotation(pitch * u - fall * 1.42 * (.5 + .5 * u), 3, 'X') @ d; d.z *= 1 - fall; d.normalize(); nxt = pts[i + 1] + L[i] * np.array(d)
            if fall and nxt[2] < .17:
                dz = np.clip(.17 - pts[i + 1, 2], -L[i] * .95, L[i] * .95); nxt = pts[i + 1] + norm(np.array([d.x, d.y, 0])) * math.sqrt(L[i] ** 2 - dz ** 2) + [0, 0, dz]
            pts[i] = nxt
        else:
            yaw = wave * math.sin(phase - u * 5) * (.25 + .75 * u) + fall * .55 * u
            d = Matrix.Rotation(yaw, 3, 'Z') @ d
            curl = (.22 * strike + .17 * hit) * u * u; d = Matrix.Rotation(curl, 3, 'X') @ d; pts[i + 1] = pts[i] + L[i] * np.array(d)
    st = held(role, t) if MODE != 'original' else None
    M = {'Root': R['Root'].copy()}; M['Root'].translation = Vector(pts[K])
    for i in range(len(L)):
        n = f'Serpent_{i:02d}'; a, b = (pts[i + 1], pts[i]) if i < K else (pts[i], pts[i + 1]); old = Vector(np.array(B[n]['tail']) - np.array(B[n]['head'])); M[n] = mat(old.rotation_difference(Vector(b - a)).to_matrix() @ R[n].to_3x3(), a)
    for n, b in B.items():
        if n in M:
            continue
        m = M[b['parent']] @ REL[n]
        if n in ['B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head']:
            angle = (-.045 * hit - .025 * wind) if n.startswith('B_Spine') else .05 * hit + .035 * strike if n == 'B_Head' else 0
            carry = M['B_Pelvis'].to_3x3() @ R['B_Pelvis'].to_3x3().transposed()
            if angle:
                m = mat(carry @ Matrix.Rotation(angle, 3, 'X') @ carry.transposed() @ m.to_3x3(), m.translation)
        if st is not None and n in ('B_L_Clavicle', 'B_R_Clavicle'):
            # the shoulder follows the Raven Man's (protraction in the wind-up), at most 30 degrees of clavicle swing
            sd = n[2]; chest = M['B_Spine2'] @ R['B_Spine2'].inverted(); h = Vector(m.translation)
            s0 = (m @ REL[f'B_{sd}_UpperArm']).translation - h; s1 = chest @ Vector(st[f'{sd}_shoulder']) - h
            q = s0.rotation_difference(s1); ang = min(q.angle, math.radians(30))
            if q.angle > 1e-6:
                m = mat(Quaternion(q.axis, ang).to_matrix() @ m.to_3x3(), h)
        M[n] = m
    carrier = M['B_Spine2'] @ R['B_Spine2'].inverted(); cr = carrier.to_3x3()
    if MODE == 'original':
        axis = norm(A0 + np.array([.20 * wind + .60 * strike + .70 * fidget + .55 * hit + .5 * cast, .12 * strike + .04 * cast + .20 * fidget, .4 * wind + .55 * strike + .6 * fidget + .65 * hit + .4 * cast]))
        center = C0 + np.array([-.15 * fidget, -.04 * wind - .09 * strike - .06 * hit - .12 * cast - .12 * fidget - .08 * math.sin(math.pi * fidget), .13 * wind + .33 * strike + .16 * fidget + .34 * hit + .28 * cast])
        if gait:
            center += np.array([0, .018 * math.sin(phase), .012 * math.cos(phase)])
        poles = {'L': np.array([.60, .13, 1.50]), 'R': np.array([-.60, .13, 1.50])}; side = None; wdirs = None
    else:
        axis = st['axis']; center = st['mid'] - axis * (S_R + S_L) / 2; side = st['side']
        # keep both fists and wrists (23 cm from the shaft) in front of the torso: push the spear forward by the largest intrusion
        push = 0.
        for s_ in (S_R, S_L):
            c = center + axis * s_
            if abs(c[0]) < .25:
                push = max(push, c[1] - (front_y(c[2]) - .23))
        if push > 0:
            center = center - np.array([0, push, 0])
        poles = {'L': st['L_elbow'], 'R': st['R_elbow']}; wdirs = {'L': st['L_wdir'], 'R': st['R_wdir']}
    wc = np.array(carrier @ Vector(center)); wa = norm(np.array(cr @ Vector(axis)))
    if MODE != 'original' and role == 'Cast':
        # the Fire Bolt leaves from Polearm [0, 0.58, 0]: keep it no higher than the installed release (2.21 m), inside
        # the existing launch bounds, by lowering the raised spear
        over = (wc + wa * .58)[2] - 2.22
        if over > 0:
            wc = wc - np.array([0, 0, over])
    if MODE != 'original':
        # Where a contact is beyond the Salamander's arm plus hand (the left hand across to the raised shaft in the
        # wind-up), shift the whole spear towards that shoulder by the shortfall.
        for _ in range(6):
            for sd in 'LR':
                hn = f'B_{sd}_Hand'; grip = G[sd]
                ar = R[hn].to_3x3() @ Vector(grip['handle_axis_hand_local']); nr = R[hn].to_3x3() @ Vector(grip['palm_normal_hand_local'])
                hr0 = frame(wa, np.array(cr @ Vector((0, 1, 0)))) @ frame(ar, nr).transposed() @ R[hn].to_3x3()
                off = -np.array(hr0 @ Vector(grip['handle_centre_hand_local'])); alpha = np.dot(off, wa); rho = np.linalg.norm(off - wa * alpha)
                sh = np.array(M[f'B_{sd}_UpperArm'].translation); c = wc + wa * (S_R if sd == 'R' else S_L); dv = sh - c
                along = np.dot(dv, wa); radial = np.linalg.norm(dv - wa * along)
                best = math.hypot(max(radial - rho, 0), along - alpha)  # nearest wrist position over all grip rolls
                reach = (np.linalg.norm(np.array(B[f'B_{sd}_Forearm']['head']) - B[f'B_{sd}_UpperArm']['head'])
                         + np.linalg.norm(np.array(B[hn]['head']) - B[f'B_{sd}_Forearm']['head']) - .03)
                if best > reach:
                    wc = wc + norm(dv) * (best - reach)
    held_wc = wc.copy(); held_wa = wa.copy()
    release = ss((t - .24) / .36) if role == 'Death' else 0
    if release:
        arc = np.array([-.20, -.65, 0]) if MODE == 'original' else np.array([-.30, -.80, .10])  # wider arc: the new grip starts the shaft lower
        wc = (1 - release) * wc + release * np.array([-1.05, -.70, .04]) + arc * math.sin(math.pi * release); wa = norm((1 - release) * wa + release * np.array([-.6, -.8, 0]))
    if side is None or release:
        px = norm(np.cross([0, 1, 0], wa))
        if np.linalg.norm(px) < .1:
            px = np.array([1., 0, 0])
        if side is not None:
            ps = norm(np.array(cr @ Vector(side))); ps = norm(ps - wa * np.dot(ps, wa)); px = norm((1 - release) * ps + release * px)
    else:
        px = norm(np.array(cr @ Vector(side))); px = norm(px - wa * np.dot(px, wa))
    proprot = Matrix(np.column_stack([px, np.cross(wa, px), wa])); M['Polearm'] = mat(proprot @ R['Polearm'].to_3x3(), wc)
    errors = []; twists = []
    for sd, sgn in [('L', 1), ('R', -1)]:
        un, fn, tn, hn = ['B_' + sd + '_' + x for x in ['UpperArm', 'Forearm', 'ForearmTwist', 'Hand']]; grip = G[sd]
        ar = R[hn].to_3x3() @ Vector(grip['handle_axis_hand_local']); nr = R[hn].to_3x3() @ Vector(grip['palm_normal_hand_local'])
        desirednormal = np.array(cr @ Vector((0, 1 if sd == 'L' else -1, 0))); hr = frame(held_wa, desirednormal) @ frame(ar, nr).transposed() @ R[hn].to_3x3()
        if wdirs is not None:
            # Roll the fitted grip about the shaft so the wrist sits where the Raven Man's does, then search +-60 degrees
            # around that roll for the least wrist bend (the Salamander's hand is longer): reach is a hard limit, the
            # departure from the Raven Man's roll and the change from the previous frame are penalised.
            contact0 = held_wc + held_wa * (S_R if sd == 'R' else S_L); sh = np.array(M[un].translation)
            ua = np.linalg.norm(np.array(B[fn]['head']) - B[un]['head']); fa = np.linalg.norm(np.array(B[hn]['head']) - B[fn]['head'])
            w = -np.array(hr @ Vector(grip['handle_centre_hand_local'])); w = norm(w - held_wa * np.dot(w, held_wa))
            want = np.array(cr @ Vector(wdirs[sd])); want = norm(want - held_wa * np.dot(want, held_wa))
            r0 = math.atan2(np.dot(np.cross(w, want), held_wa), np.dot(w, want)); base_hr = hr
            pole0 = np.array(carrier @ Vector(poles[sd])); best = None
            for dd in range(-60, 61, 5):
                h_ = Matrix.Rotation(r0 + math.radians(dd), 3, Vector(held_wa)) @ base_hr
                wr = contact0 - np.array(h_ @ Vector(grip['handle_centre_hand_local'])); v_ = wr - sh; dist_ = np.linalg.norm(v_)
                over = max(0., dist_ - (ua + fa - .004)); dist_c = min(max(dist_, abs(ua - fa) + .003), ua + fa - .004); dr = v_ / max(dist_, 1e-9)
                pl = pole0 - sh; pl = norm(pl - dr * np.dot(pl, dr)); al = (ua * ua - fa * fa + dist_c * dist_c) / (2 * dist_c)
                el = sh + dr * al + pl * math.sqrt(max(0, ua * ua - al * al)); wr_c = sh + dr * dist_c
                kn = np.array(h_ @ KNUCKLE[sd]); bend = abs(math.degrees(math.acos(np.clip(np.dot(norm(kn), norm(wr_c - el)), -1, 1))) - REST_BEND[sd])
                fsw = (cr @ Vector(np.array(B[hn]['head']) - B[fn]['head'])).rotation_difference(Vector(wr_c - el)).to_matrix() @ cr @ R[fn].to_3x3()
                q_ = (h_ @ R[hn].to_3x3().transposed() @ (fsw @ R[fn].to_3x3().transposed()).transposed()).to_quaternion()
                tw_ = abs(math.degrees(2 * math.atan2(Vector((q_.x, q_.y, q_.z)).dot(Vector(norm(wr_c - el))), q_.w)))
                tw_ = 360 - tw_ if tw_ > 180 else tw_
                cost = bend + .5 * abs(dd) + 3 * max(0., tw_ - 86) + 1e4 * over  # deterministic per pose: loops close
                if best is None or cost < best[0]:
                    best = (cost, dd, h_)
            PREV[(role, sd)] = best[1]; hr = best[2]
            if os.environ.get('SPEAR_DEBUG') and role == 'Attack' and abs(t - .875) < .01:
                print('ROLL', sd, best[1], round(best[0], 1))
        contact = held_wc + held_wa * (S_R if sd == 'R' else S_L); target = Vector(contact) - hr @ Vector(grip['handle_centre_hand_local'])
        free = fidget if sd == 'L' else 0
        free = max(free, release)
        if free:
            resttarget = Vector((sgn * (.75 if release else .47), .10 if release else -.18, 1.98 if not release else 1.32)); held_target = target.copy(); target = target.lerp(carrier @ resttarget, free)
            if MODE != 'original' and not release:
                # Fidget: the lifted fist keeps its wrist angle to the forearm (the rest-orientation slerp of the
                # original turned the re-rolled grip through a 50-degree twist jump)
                sh_ = np.array(M[un].translation)
                def fore(tg):
                    ua = np.linalg.norm(np.array(B[fn]['head']) - B[un]['head']); fa = np.linalg.norm(np.array(B[hn]['head']) - B[fn]['head'])
                    v_ = np.array(tg) - sh_; d_ = min(max(np.linalg.norm(v_), abs(ua - fa) + .003), ua + fa - .002); dr = norm(v_)
                    pl = np.array(carrier @ Vector(poles[sd])) - sh_; pl = norm(pl - dr * np.dot(pl, dr)); al = (ua * ua - fa * fa + d_ * d_) / (2 * d_)
                    el = sh_ + dr * al + pl * math.sqrt(max(0, ua * ua - al * al))
                    return (cr @ Vector(np.array(B[hn]['head']) - B[fn]['head'])).rotation_difference(Vector(sh_ + dr * d_ - el)).to_matrix()
                hr = fore(target) @ fore(held_target).transposed() @ hr  # same swing frame as the forearm bone below
            else:
                hr = hr.to_quaternion().slerp((cr @ R[hn].to_3x3()).to_quaternion(), free).to_matrix()
        shoulder = np.array(M[un].translation); restE = Vector(B[fn]['head']); restW = Vector(B[hn]['head']); a = np.linalg.norm(np.array(restE) - B[un]['head']); b = np.linalg.norm(np.array(restW - restE)); v = np.array(target) - shoulder; distance = np.linalg.norm(v); dist = np.clip(distance, abs(a - b) + .003, a + b - .002); direction = norm(v); target = Vector(shoulder + direction * dist)
        errors.append(abs(distance - dist) * (1 - free))
        if os.environ.get('SPEAR_DEBUG') and abs(distance - dist) * (1 - free) > .01:
            print('REACH', role, round(t, 3), sd, round(distance, 3), 'reach', round(a + b, 3))
        pole = np.array(carrier @ Vector(poles[sd])) - shoulder; pole = norm(pole - direction * (pole @ direction)); along = (a * a - b * b + dist * dist) / (2 * dist); elbow = shoulder + direction * along + pole * math.sqrt(max(0, a * a - along * along))
        for n, start, end, restend in [(un, shoulder, elbow, B[fn]['head']), (fn, elbow, np.array(target), B[hn]['head'])]:
            orig = cr @ Vector(np.array(restend) - B[n]['head']); rot = orig.rotation_difference(Vector(end - start)).to_matrix() @ cr @ R[n].to_3x3(); M[n] = mat(rot, start)
        delta = hr @ R[hn].to_3x3().transposed() @ (M[fn].to_3x3() @ R[fn].to_3x3().transposed()).transposed(); q = delta.to_quaternion(); axisfore = (target - Vector(elbow)).normalized(); v = Vector((q.x, q.y, q.z)); amount = v.dot(axisfore); angle = 2 * math.atan2(amount, q.w); angle = (angle + math.pi) % (2 * math.pi) - math.pi; twists.append(abs(angle))
        base = M[fn].to_3x3(); M[fn] = mat(Matrix.Rotation(angle * .25, 3, axisfore) @ base, elbow); M[tn] = mat(Matrix.Rotation(angle * .75, 3, axisfore) @ base, (Vector(elbow) + target) / 2); M[hn] = mat(hr, target)
        for f in range(5):
            for suffix in ['', '1', '2']:
                n = f'B_{sd}_Finger{f}' + suffix; quat = Quaternion(grip['finger_local'][n]); quat = Quaternion().slerp(quat, 1 - .75 * release); M[n] = M[B[n]['parent']] @ REL[n] @ quat.to_matrix().to_4x4()
    for n in B:
        parent = B[n]['parent']; rig.pose.bones[n].matrix_basis = REL[n].inverted() @ (M[parent].inverted() @ M[n] if parent else M[n])
    bpy.context.view_layer.update(); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh(); floor = min(v.co.z for v in me.vertices); ev.to_mesh_clear(); lift = max(0, -floor)
    if lift:
        rig.pose.bones['Root'].location += R['Root'].to_3x3().transposed() @ Vector((0, 0, lift))
    if release:
        bpy.context.view_layer.update(); ev = weapon.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh(); low = min(v.co.z for v in me.vertices); ev.to_mesh_clear()
        if low < .018 or release > .999:
            pb = rig.pose.bones['Polearm']; world = pb.matrix.copy(); world.translation.z += .018 - low; pb.matrix = world
    bpy.context.view_layer.update()
    return {'grip_error': max(errors), 'forearm_twist': max(twists), 'fall': fall}


Cv = np.array([v.co[:] for v in body.data.vertices]); E = np.array([e.vertices[:] for e in body.data.edges]); EL = np.linalg.norm(Cv[E[:, 1]] - Cv[E[:, 0]], axis=1); valid = EL > .001; reports = {}
for old in list(bpy.data.actions):
    bpy.data.actions.remove(old)
for role, duration in DUR.items():
    count = round(duration * FPS); keys = {n: [] for n in B}; floors = []; errors = []; ratios = []; twists = []; first = last = None
    for frameidx in range(count + 1):
        rig.animation_data_clear(); metrics = pose(role, frameidx / FPS); errors.append(metrics['grip_error']); twists.append(metrics['forearm_twist'])
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh(); c = np.array([v.co[:] for v in me.vertices]); ev.to_mesh_clear()
        first = c.copy() if first is None else first; last = c; floors.append(float(c[:, 2].min())); ratio = np.linalg.norm(c[E[:, 1]] - c[E[:, 0]], axis=1) / np.maximum(EL, 1e-8); ratios.append([float(np.percentile(ratio[valid], 99)), float(ratio[valid].max())])
        for n in B:
            pb = rig.pose.bones[n]; quat = pb.rotation_quaternion.copy()
            if keys[n] and quat.dot(keys[n][-1][1]) < 0:
                quat.negate()
            keys[n].append((pb.location.copy(), quat))
    action = bpy.data.actions.new(role); action.use_fake_user = True; rig.animation_data_create(); rig.animation_data.action = action
    for frameidx in range(count + 1):
        for n in B:
            pb = rig.pose.bones[n]; pb.location, pb.rotation_quaternion = keys[n][frameidx]; pb.keyframe_insert('location', frame=frameidx + 1, group=n); pb.keyframe_insert('rotation_quaternion', frame=frameidx + 1, group=n)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'LINEAR'
    reports[role] = {'duration': count / FPS, 'min_z': min(floors), 'grip_target_error': max(errors), 'max_forearm_twist_degrees': math.degrees(max(twists)), 'loop_delta': float(np.linalg.norm(last - first, axis=1).max()), 'stretch_p99_max': np.max(ratios, axis=0).tolist()}
    print(role, reports[role], flush=True)
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(1)
tag = os.environ.get('SPEAR_TAG', MODE)
bpy.ops.wm.save_as_mainfile(filepath=str(P / f'work/spear_{tag}.blend'))
(P / f'work/spear_{tag}_audit.json').write_text(json.dumps({'mode': MODE, 'S_R': S_R, 'S_L': S_L, 'arm_scale': KS, 'clips': reports}, indent=2) + '\n')
print('SAVED', tag, 'arm scale', round(KS, 4))
