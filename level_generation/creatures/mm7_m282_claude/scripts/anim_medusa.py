"""Procedural Medusa clips (30 fps) on work/rig_v2.blend -> work/anim_v1.blend (+ work/clips.json, work/arm_log.json).

Serpent (quadruped playbook "Snakes", mm6_cob_claude/scripts/anim_cob.py): every frame defines the centreline - the
tail branch on the floor (each joint at its rest height, heading integrated from a curvature profile, frames locked to
world up), the column branch by per-segment pitch/yaw of its rest direction with a floor rule and a twist carried up to
the hips - and fits the axial bones to it.
Upper body (humanoid playbook): spine/neck/head by local rotations; arms by two-bone hinge IK (posing.two_bone_ik_hinge:
the elbow only flexes about the forearm's own axis, so the elbow never twists) to wrist targets set in the chest frame or
in the world (the aim), hand orientation set explicitly, 60 % of the hand roll on ForeArmTwist, finger curls (bow fist
solved once around the handle). Key poses follow the native frames (m282*), timings the native descriptors:
  Standing 2.625 s loop (3 x the native 0.875 s idle)   Walking 0.875 s loop (native)   Running 0.7 s loop
  Attack   1.5 s (native 1.25 s: reach to the quiver, raise, nock, draw, hold af 0.625-1.0 s, RELEASE 1.0 s; recovery
           eased into Standing)                          Hit 0.75 s (native)
  Death    1.5 s (native 0.875 s + settle) Dead = last Death pose held   Fidget 2.0 s (head turns, bow check)
Floor rules every frame: column joints >= their radius; hands/forearms kept above the floor; corpse torso grounded by a
measured lift of the pelvis.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as PO
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(HERE, 'work', *p)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
FPS = 30
D = json.load(open(W('rig.json'))); BR = json.load(open(W('bow_rig.json'))); HS = json.load(open(W('hands.json')))
J0 = np.array(D['axial']); RAD = np.array(D['radius']); K = D['root']; NAMES = D['names']; NSEG = len(NAMES)
L = np.linalg.norm(np.diff(J0, axis=0), axis=1)
COL = list(range(K, NSEG)); TAIL = list(range(K - 1, -1, -1))
REST_DIR = {i: Vector(J0[i] - J0[i + 1]).normalized() if i < K else Vector(J0[i + 1] - J0[i]).normalized() for i in range(NSEG)}
TAIL_LEN = float(L[:K].sum())
X_, Y_, Z_ = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
FINGERS = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
STRIDE_WALK, STRIDE_RUN, RELEASE = 1.6, 2.1, 1.0
IMPACT = RELEASE
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


# ================================================================== serpent
def frames(P, twist):
    def seg_dir(i):
        v = Vector(P[i] - P[i + 1]) if i < K else Vector(P[i + 1] - P[i]); return v.normalized()
    F = {}
    t = seg_dir(K)
    t0 = REST_DIR[K]; n0 = (X_ - X_.dot(t0) * t0).normalized()
    n = t0.rotation_difference(t) @ n0                       # root frame transported from its rest (no flip when lying)
    n = (n - n.dot(t) * t).normalized()
    F[K] = (t, n); pt, pn = t, n
    for idx, i in enumerate(COL[1:]):
        ti = seg_dir(i); q = pt.rotation_difference(ti)
        ni = q @ pn; ni = (ni - ni.dot(ti) * ti).normalized()
        pt, pn = ti, ni
        F[i] = (ti, ni)
    out_ = {}
    for idx, i in enumerate(COL):
        t, n = F[i]
        if twist is not None:
            n = Quaternion(t, twist[idx]) @ n
        out_[i] = Matrix((t, n, t.cross(n))).transposed()
    for i in TAIL:
        ti = seg_dir(i); side = Z_.cross(ti)
        n = side.normalized() if side.length > 1e-6 else X_
        out_[i] = Matrix((ti, n, ti.cross(n))).transposed()
    return out_


REST_F = frames(J0, None)
REST_M = {n: rig.data.bones[n].matrix_local.copy() for n in NAMES}
PARENT = {n: (rig.data.bones[n].parent.name if rig.data.bones[n].parent else None) for n in NAMES}


def curve(col_pitch=None, col_yaw=None, kappa=None, tail_heading=0.0, root_offset=(0, 0, 0), tail_lift=None,
          col_dirs=None, floor_top=0.0):
    P = J0.copy(); P[K] = J0[K] + np.array(root_offset)
    for idx, i in enumerate(COL):
        if col_dirs is not None:
            d = col_dirs[idx]
        else:
            d = Matrix.Rotation(col_yaw[idx] if col_yaw else 0.0, 3, 'Z') @ \
                Matrix.Rotation(col_pitch[idx] if col_pitch else 0.0, 3, 'X') @ REST_DIR[i]
        nxt = np.array(P[i]) + L[i] * np.array(d)
        floor = max(RAD[i + 1] * 0.95, floor_top * (1.0 - 0.3 * idx / max(NC - 1, 1)))
        if nxt[2] < floor:
            h = np.array([d[0], d[1], 0.0]); hn = np.linalg.norm(h); h = h / hn if hn > 1e-6 else np.array([0, -1.0, 0])
            dz = floor - P[i][2]
            nxt = np.array(P[i]) + h * math.sqrt(max(L[i] ** 2 - dz * dz, 1e-6)) + np.array([0, 0, dz])
        P[i + 1] = nxt
    heading = tail_heading
    for m, i in enumerate(TAIL):
        if kappa is not None:
            heading += kappa[m] * L[i]
        z1 = max(J0[i][2], RAD[i] * 0.95) + (tail_lift[m] if tail_lift is not None else 0.0)
        dz = z1 - P[i + 1][2]; hl = math.sqrt(max(L[i] ** 2 - dz * dz, 1e-6))
        P[i] = P[i + 1] + np.array([math.sin(heading) * hl, math.cos(heading) * hl, dz])
    return P


def apply_axial(P, twist):
    F = frames(P, twist); pose = {}
    for i, n in enumerate(NAMES):
        rot = F[i] @ REST_F[i].transposed()
        head = P[i + 1] if i < K else P[i]
        m = (rot @ REST_M[n].to_3x3()).to_4x4(); m.translation = Vector(head); pose[n] = m
    for n in NAMES:
        rest = REST_M[n]; p = PARENT[n]
        if p is None:
            basis = rest.inverted() @ pose[n]
        else:
            basis = (REST_M[p].inverted() @ rest).inverted() @ pose[p].inverted() @ pose[n]
        rig.pose.bones[n].matrix_basis = basis
    bpy.context.view_layer.update()


def profile(total, n, power=1.0):
    return [total * ((k + 1) / n) ** power for k in range(n)]


NC = len(COL)
REST_HEADING = 0.0


def tail_straight(t=0.0, amp=0.0, lam=1.0, T=1.0, curl=0.0):
    """kappa per tail segment: a travelling wave (amp 1/m) plus a constant curl; mean heading kept straight back"""
    v = np.cumsum(L[K - 1::-1]) - L[K - 1] / 2
    k = amp * np.sin(2 * math.pi * (v / lam + t / T)) * np.clip((v - 0.3) / 0.5, 0, 1) + curl
    head = np.cumsum(k * L[K - 1::-1]); h0 = -float(np.mean(head)) * (1 if amp else 0)
    return k, h0


# ================================================================== upper body
def pbm(n):
    return rig.matrix_world @ rig.pose.bones[n].matrix


def chest():
    M = pbm('Spine2'); R = M.to_3x3().normalized()
    return R.col[0].normalized(), R.col[1].normalized(), R.col[2].normalized()          # left, up, forward


def rotl(n, axis, deg):
    if abs(deg) > 1e-6:
        PO.rotate_local(rig, n, axis, deg)


def torso(lean=0.0, turn=0.0, side=0.0, head_pitch=0.0, head_yaw=0.0, head_roll=0.0):
    for n, w in (('Pelvis', 0.35), ('Spine1', 0.35), ('Spine2', 0.3)):
        rotl(n, 'X', lean * w); rotl(n, 'Y', turn * w); rotl(n, 'Z', side * w)
    for n, w in (('Neck', 0.4), ('Head', 0.6)):
        rotl(n, 'X', head_pitch * w); rotl(n, 'Y', head_yaw * w); rotl(n, 'Z', head_roll * w)


def look_at(target, amount=1.0):
    """turn Neck (40 %) and Head (60 %) so the face (Head local Z) points at a world target"""
    for n, w in (('Neck', 0.4), ('Head', 1.0)):
        M = pbm('Head'); fwd = M.to_3x3().col[2].normalized(); head = M.translation + M.to_3x3().col[1] * 0.08
        want = (Vector(target) - head).normalized()
        q = Quaternion().slerp(fwd.rotation_difference(want), amount * w)
        ax, ang = q.to_axis_angle()
        if abs(ang) > 1e-5:
            PO.rotate_world(rig, n, ax, math.degrees(ang))


def hand_frame(Yd, side, I=None, Zd=None):
    """hand rotation from the knuckle direction Yd and either the index-side direction I or the palm normal Zd.
    The hand bones are mirrored: local X is the index side on the right hand and the pinky side on the left."""
    Yd = Vector(Yd).normalized()
    if I is not None:
        Xd = Vector(I) * (1 if side == 'R' else -1); Xd = (Xd - Yd * Xd.dot(Yd)).normalized(); Zd = Xd.cross(Yd)
    else:
        Zd = Vector(Zd); Zd = (Zd - Yd * Zd.dot(Yd)).normalized(); Xd = Yd.cross(Zd)
    return Matrix((Xd, Yd, Zd)).transposed()


ARMLOG = {}
HAIR_LOW = []
PREV_TW = {}
TW_MAX, SW_MAX = math.radians(100), math.radians(60)


SWIVEL = list(range(-100, 101, 10))
MODE = {'m': 'final'}
PLAN = {}
CHOSEN = {}


def arm_math(side, target, pole, hand_spec, prev_tw=None):
    """pure math: hinge-exact two-bone IK - the elbow flexion phi (about the forearm's own local X, carrying angle
    kept) from the shoulder-wrist distance, the rigid bent arm turned about the shoulder so the wrist reaches the target
    and the elbow points toward the pole - and the hand's twist/swing relative to the forearm"""
    ub = rig.pose.bones[f'UpperArm_{side}']; lbb = rig.pose.bones[f'ForeArm_{side}']; hb = rig.pose.bones[f'Hand_{side}']
    la = ub.bone.length; lb_len = lbb.bone.length
    Rrel = (ub.bone.matrix_local.inverted() @ lbb.bone.matrix_local).to_3x3()
    Rh = (lbb.bone.matrix_local.inverted() @ hb.bone.matrix_local).to_3x3()
    wl = lambda phi: Vector((0, la, 0)) + lb_len * (Rrel @ Matrix.Rotation(phi, 3, 'X') @ Vector((0, 1, 0)))
    S = rig.matrix_world @ ub.head
    dist = (target - S).length
    lo, hi = 0.0, math.radians(160)
    d = min(max(dist, wl(hi).length), wl(lo).length)
    for _ in range(30):
        mid = (lo + hi) / 2
        if wl(mid).length > d:
            lo = mid
        else:
            hi = mid
    phi = (lo + hi) / 2
    W_ = wl(phi); a1 = W_.normalized(); e = Vector((0, la, 0)); b1 = (e - a1 * e.dot(a1)).normalized()
    a2 = (target - S).normalized(); pv = pole - S; b2 = (pv - a2 * pv.dot(a2))
    if b2.length < 1e-6:
        b2 = Vector((0, 0, 1)) - a2 * a2.z
    b2.normalize()
    Q = Matrix((a2, b2, a2.cross(b2))).transposed() @ Matrix((a1, b1, a1.cross(b1))).transposed().inverted()
    Fr = Q @ Rrel @ Matrix.Rotation(phi, 3, 'X')
    natural = Fr @ Rh
    a = (Fr @ Vector((0, 1, 0))).normalized()

    def decompose(R):
        q = (R @ natural.inverted()).to_quaternion()
        if q.w < 0:
            q = -q
        t = 2 * math.atan2(Vector(q[1:]).dot(a), q.w)
        return t, Quaternion(a, t).inverted() @ q

    def resolve(spec):
        if not isinstance(spec, tuple):
            return spec
        if spec[0] in ('dir', 'dirf'):                        # ('dir', knuckle direction, roll deg): minimal-twist hand
            _, yd, roll = spec; ny = natural.col[1].normalized()    # 'dir' goes half way from the forearm, 'dirf' fully
            yd = ny.lerp(Vector(yd).normalized(), 0.5 if spec[0] == 'dir' else 1.0).normalized() if yd is not None else ny
            return (Quaternion(yd, math.radians(roll)) @ ny.rotation_difference(yd)).to_matrix() @ natural
        _, A, B, f = spec                                      # ('mix', A, B, f): twist and swing interpolated
        tA, sA = decompose(resolve(A)); tB, sB = decompose(resolve(B))
        tB = tA + math.remainder(tB - tA, 2 * math.pi)
        if prev_tw is not None:                                # branches of A and B that keep the blend continuous
            tA, tB = min(((tA + i * 2 * math.pi, tB + j * 2 * math.pi) for i in (-1, 0, 1) for j in (-1, 0, 1)),
                         key=lambda x: abs(lerp(x[0], x[1], f) - prev_tw) + 0.05 * (abs(x[0] - tA) + abs(x[1] - tB)))
        return (Quaternion(a, lerp(tA, tB, f)) @ sA.slerp(sB, f)).to_matrix() @ natural
    tw, swing = decompose(resolve(hand_spec))
    return dict(S=S, Q=Q, Fr=Fr, phi=phi, natural=natural, a=a, tw=tw, swing=swing, reach_err=dist - d)


def swivel_pole(target, pole, S, deg):
    ax = (target - S).normalized()
    return S + Quaternion(ax, math.radians(deg)) @ (pole - S)


def arm(side, wrist, pole, hand_rot, clav=(0.0, 0.0), log=None):
    """clav: (elevation, protraction) in metres of the clavicle tip in the chest frame. The elbow swivel about the
    shoulder-wrist axis is chosen over the whole clip (plan pass + dynamic programming, playbook arm_dp): cost = forearm
    twist + wrist swing beyond 35 deg + distance from the authored pole, plus a continuity penalty."""
    wrist, pole = Vector(wrist), Vector(pole)
    lat, up, fwd = chest()
    cb = rig.pose.bones[f'Clavicle_{side}']
    if abs(clav[0]) + abs(clav[1]) > 1e-6:
        tip = rig.matrix_world @ cb.tail
        PO.aim_bone(rig, f'Clavicle_{side}', tip + up * clav[0] + fwd * clav[1])
    S = rig.matrix_world @ rig.pose.bones[f'UpperArm_{side}'].head
    idx = len(log.get(side, [])) if log is not None else None
    if MODE['m'] == 'plan' and log is not None:
        costs = []
        for o in SWIVEL:
            m = arm_math(side, wrist, swivel_pole(wrist, pole, S, o), hand_rot, None)
            sw = math.degrees(m['swing'].angle if m['swing'].angle <= math.pi else 2 * math.pi - m['swing'].angle)
            tw = abs(math.degrees(m['tw']))
            costs.append(0.6 * tw + max(0.0, tw - 80) * 3 + max(0.0, sw - 35) * 1.5 + 0.25 * abs(o))
        PLAN.setdefault(side, []).append(costs)
        PLAN_TW[side] = arm_math(side, wrist, pole, hand_rot, PLAN_TW.get(side))['tw']
    off = 0
    if MODE['m'] == 'final':
        ch = CHOSEN.get(side)
        if ch:
            j = idx if idx is not None else PENDING.get(side, 0)
            off = ch[min(j, len(ch) - 1)]
    m = arm_math(side, wrist, swivel_pole(wrist, pole, S, off), hand_rot, PREV_TW.get(side))
    ub = rig.pose.bones[f'UpperArm_{side}']; fa = rig.pose.bones[f'ForeArm_{side}']; hb = rig.pose.bones[f'Hand_{side}']
    inv = rig.matrix_world.inverted()
    ub.matrix = Matrix.LocRotScale(inv @ m['S'], (inv.to_3x3() @ m['Q']).to_quaternion(), Vector((1, 1, 1)))
    bpy.context.view_layer.update()
    fa.matrix = Matrix.LocRotScale(fa.head.copy(), (inv.to_3x3() @ m['Fr']).to_quaternion(), Vector((1, 1, 1)))
    bpy.context.view_layer.update()
    a = m['a']; tw = m['tw']; natural = m['natural']
    prev = PREV_TW.get(side)
    if prev is not None:                                      # continuity: unwrap the twist toward the previous frame
        tw = prev + math.remainder(tw - prev, 2 * math.pi)
    tw = max(-TW_MAX, min(TW_MAX, tw))
    sax, sang = m['swing'].to_axis_angle()
    if sang > math.pi:
        sang -= 2 * math.pi
    sang = max(-SW_MAX, min(SW_MAX, sang))
    swing = Quaternion(sax, sang)
    if log is not None:
        PREV_TW[side] = tw
    hand_q = ((Quaternion(a, tw) @ swing).to_matrix() @ natural).to_quaternion()
    hb.matrix = Matrix.LocRotScale(hb.head.copy(), (inv.to_3x3() @ hand_q.to_matrix()).to_quaternion(), Vector((1, 1, 1)))
    bpy.context.view_layer.update()
    PO.rotate_world(rig, f'ForeArmTwist_{side}', a, math.degrees(0.6 * tw))
    PREV_IK[side] = (math.degrees(m['phi']), round(100 * m['reach_err'], 1), off)
    swing_deg = math.degrees(abs(sang))
    if log is not None:
        log.setdefault(side, []).append((round(math.degrees(tw), 1), round(swing_deg, 1), round(PREV_IK[side][0]), off))
    return tw, swing_deg


PENDING = {}
PLAN_TW = {}


def plan_swivels():
    CHOSEN.clear()
    for side, rows in PLAN.items():
        C = np.array(rows); n, k = C.shape; acc = C[0].copy(); back = np.zeros((n, k), int)
        O = np.array(SWIVEL, float)
        T = 2.5 * np.abs(O[:, None] - O[None, :])
        for i in range(1, n):
            tot = acc[:, None] + T                     # from j to k'
            back[i] = np.argmin(tot, 0); acc = tot[back[i], np.arange(k)] + C[i]
        path = [int(np.argmin(acc))]
        for i in range(n - 1, 0, -1):
            path.append(int(back[i][path[-1]]))
        CHOSEN[side] = [SWIVEL[j] for j in path[::-1]]
    PLAN.clear()


PREV_IK = {}


def curl(side, amounts):
    """amounts: {finger: (a1, a2, a3)} degrees about each bone's flexion axis (+ = toward the palm)"""
    for f, (a1, a2, a3) in amounts.items():
        for k, a in enumerate((a1, a2, a3)):
            rotl(f'{f}{k + 1}_{side}', 'X', a)


FIST = {'Thumb': (25, 30, 25), 'Index': (55, 75, 45), 'Middle': (60, 80, 45), 'Ring': (62, 80, 45), 'Pinky': (65, 80, 45)}
RELAX = {'Thumb': (5, 10, 8), 'Index': (12, 18, 12), 'Middle': (14, 20, 12), 'Ring': (16, 22, 14), 'Pinky': (18, 24, 14)}
HOOK = {'Thumb': (20, 25, 15), 'Index': (25, 55, 35), 'Middle': (25, 55, 35), 'Ring': (30, 60, 40), 'Pinky': (60, 75, 45)}
OPEN = {f: (0, 3, 3) for f in FINGERS}
PINCH = {'Thumb': (30, 35, 20), 'Index': (30, 45, 30), 'Middle': (35, 55, 35), 'Ring': (55, 70, 45), 'Pinky': (65, 80, 45)}


def blend_curl(a, b, t):
    return {f: tuple(lerp(x, y, t) for x, y in zip(a[f], b[f])) for f in FINGERS}


# ------------------------------------------------------------------ bow and arrow bones
NOCK = Vector(BR['nock_bow']); REST_ARROW = Vector(BR['rest_bow']); ARROW_LEN = BR['arrow_len']
QUIVER_UP = Vector((-0.25, 0.5, 0.95)).normalized()            # quiver axis out of its mouth (rest, chest-ish frame)


def bow_world():
    return pbm('Bow')


def set_string(draw, creep=0.0):
    """StringNock pulled back along the bow's +X by `draw` metres beyond the braced string"""
    sn = rig.pose.bones['StringNock']
    sn.matrix_basis = Matrix.Translation(Vector((0, 0, 0)))
    bpy.context.view_layer.update()
    Bw = bow_world(); target = Bw @ (NOCK + Vector((draw, 0, 0)))
    Mn = Bw.copy(); Mn.translation = target
    sn.matrix = rig.matrix_world.inverted() @ Mn; bpy.context.view_layer.update()
    return target


def set_arrow(base, direction, up, visible=True):
    an = rig.pose.bones['Arrow']
    if not visible:
        an.matrix_basis = Matrix.Diagonal((0.0, 0.0, 0.0, 1.0)); bpy.context.view_layer.update(); return
    d = Vector(direction).normalized(); x = d.cross(Vector(up)).normalized()
    M = Matrix((x, d, x.cross(d))).transposed().to_4x4(); M.translation = Vector(base)
    an.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()


def pinch_point(side='R'):
    i2 = pbm(f'Index2_{side}').translation; m2 = pbm(f'Middle2_{side}').translation
    hz = pbm(f'Hand_{side}').to_3x3().col[2].normalized()
    return (i2 + m2) / 2 + hz * 0.008


# ================================================================== poses
def reset():
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix()
    rig.pose.bones['Arrow'].matrix_basis = Matrix.Diagonal((0.0, 0.0, 0.0, 1.0))      # hidden unless nocked/held
    bpy.context.view_layer.update()


def stand_arms(t=0.0, breathe=0.0, log=None, bow_up=0.0, right_swing=0.0):
    """native stance: bow upright in the left fist beside the hip, right hand resting on the belly"""
    lat, up, fwd = chest()
    SL = pbm('UpperArm_L').translation; SR = pbm('UpperArm_R').translation
    w = SL + lat * 0.12 + up * (-0.40 + 0.18 * bow_up) + fwd * (0.20 + 0.08 * bow_up)
    arm('L', w, SL + lat * 0.25 - up * 0.25 - fwd * 0.35, hand_frame(fwd * 0.9 - up * 0.2 * (1 - bow_up) + lat * 0.15, 'L', I=up - lat * 0.22 - fwd * 0.15),
        clav=(0.004 * breathe, 0.0), log=log)
    curl('L', FIST)
    waist = pbm('Spine1').translation
    w = waist - lat * (0.15 + 0.04 * abs(right_swing)) + fwd * (0.15 + 0.03 * right_swing) + up * (0.02 + 0.01 * breathe + 0.03 * abs(right_swing))
    arm('R', w, SR - lat * 0.45 - up * 0.1 - fwd * 0.1,
        hand_frame(lat * 0.65 - up * 0.65 + fwd * 0.25, 'R', Zd=-fwd + lat * 0.2), clav=(0.004 * breathe, 0.0), log=log)
    curl('R', RELAX)


def axial_stand(t, T=2.625, amp=1.0):
    sway = 0.035 * math.sin(2 * math.pi * t / T) * amp
    breathe = 0.02 * math.sin(2 * math.pi * 2 * t / T) * amp
    k, _ = tail_straight(curl=0.0)
    k = k + 0.18 * np.sin(np.linspace(0, math.pi, len(k)) + 2 * math.pi * t / T) * amp
    return dict(col_pitch=profile(breathe, NC), col_yaw=profile(sway, NC, 1.5), kappa=k, tail_heading=0.0)


def standing(t, log=None):
    T = 2.625; reset()
    apply_axial(curve(**axial_stand(t, T)), profile(0.03 * math.sin(2 * math.pi * t / T), NC))
    br = math.sin(2 * math.pi * 2 * t / T)
    torso(lean=1.2 * br, turn=2 * math.sin(2 * math.pi * t / T), head_pitch=-2 * br, head_yaw=-3 * math.sin(2 * math.pi * t / T))
    stand_arms(t, br, log)


def gait(t, T, stride, amp, lean, run=False, log=None):
    reset()
    lam = stride
    v = np.cumsum(L[K - 1::-1]) - L[K - 1] / 2
    k = amp * np.sin(2 * math.pi * (v / lam + t / T)) * np.clip((v - 0.25) / 0.5, 0, 1)
    head = np.cumsum(k * L[K - 1::-1]); h0 = -float(np.mean(head))
    ph = 2 * math.pi * t / T
    sway = 0.10 * math.sin(ph) * (1.4 if run else 1.0)
    bob = 0.025 * math.sin(2 * ph)
    pitch = profile(lean + bob, NC)
    yaw = [sway * math.sin(math.pi * (j + 1) / NC) for j in range(NC)]
    apply_axial(curve(col_pitch=pitch, col_yaw=yaw, kappa=k, tail_heading=h0), profile(-0.6 * sway, NC))
    torso(lean=4 if run else 1.5, turn=math.degrees(-0.5 * sway), side=math.degrees(0.35 * sway),
          head_yaw=math.degrees(0.5 * sway), head_pitch=-3 if run else 0)
    stand_arms(t, 0.0, log, bow_up=0.15 if run else 0.0, right_swing=(0.8 if run else 0.4) * math.sin(ph))


TARGET = Vector((0.0, -6.0, 1.45))                       # the party, ahead at eye height (aim slightly up from the bow)


# ------------------------------------------------------------------ attack: keyed parameters
def attack_keys():
    """(time, params). Arm targets are specs evaluated in the current chest frame:
       ('chest', side, (lat, up, fwd) from that side's shoulder) or ('aim', reach) for the bow arm"""
    return [
        (0.00, dict(turn=0, lean=0, col_turn=0.0, head=0, bowpose='stand', rpose='stand', draw=0.0, rs=0.0, arrow=0)),
        (0.10, dict(turn=-5, lean=-2, col_turn=-0.04, head=-3, bowpose='stand_up', rpose='lift', draw=0.0, rs=0.0, arrow=0)),
        (0.20, dict(turn=-10, lean=-4, col_turn=-0.08, head=-6, bowpose='stand_up', rpose='quiver', draw=0.0, rs=0.0, arrow=0)),
        (0.30, dict(turn=-14, lean=-5, col_turn=-0.12, head=-8, bowpose='raise', rpose='quiver', draw=0.0, rs=0.0, arrow=1)),
        (0.38, dict(turn=-18, lean=-4, col_turn=-0.16, head=-6, bowpose='high', rpose='overhead', draw=0.0, rs=0.0, arrow=1)),
        (0.50, dict(turn=-26, lean=-1, col_turn=-0.22, head=-2, bowpose='aim_near', rpose='bring', draw=0.0, rs=0.0, arrow=1)),
        (0.60, dict(turn=-40, lean=0, col_turn=-0.32, head=0, bowpose='aim_near', rpose='string', draw=0.0, rs=1.0, arrow=2)),
        (0.72, dict(turn=-50, lean=2, col_turn=-0.40, head=0, bowpose='aim', rpose='string', draw=0.82, rs=1.0, arrow=2)),
        (0.98, dict(turn=-52, lean=2, col_turn=-0.42, head=0, bowpose='aim', rpose='string', draw=0.85, rs=1.0, arrow=2)),
        (1.067, dict(turn=-52, lean=2, col_turn=-0.42, head=0, bowpose='aim', rpose='release', draw=0.0, rs=0.0, arrow=0)),
        (1.12, dict(turn=-46, lean=0, col_turn=-0.36, head=0, bowpose='aim_low', rpose='release2', draw=0.0, rs=0.0, arrow=0)),
        (1.28, dict(turn=-16, lean=0, col_turn=-0.12, head=0, bowpose='lower', rpose='lowerR', draw=0.0, rs=0.0, arrow=0)),
        (1.50, dict(turn=0, lean=0, col_turn=0.0, head=0, bowpose='stand', rpose='stand', draw=0.0, rs=0.0, arrow=0)),
    ]


def arm_spec(side, pose_name):
    """world wrist target, pole, hand rotation and finger curls for a named pose in the current chest frame"""
    lat, up, fwd = chest()
    S = pbm(f'UpperArm_{side}').translation
    if side == 'L':
        if pose_name in ('stand', 'stand_up'):
            b = 0.25 if pose_name == 'stand_up' else 0.0
            w = S + lat * 0.12 + up * (-0.40 + 0.18 * b) + fwd * (0.20 + 0.08 * b)
            return w, S + lat * 0.25 - up * 0.25 - fwd * 0.35, hand_frame(fwd * 0.9 - up * 0.2 * (1 - b) + lat * 0.15, 'L', I=up - lat * 0.22 - fwd * 0.15), FIST
        if pose_name == 'lower':
            w = S + lat * 0.18 - up * 0.30 + fwd * 0.30
            return w, S + lat * 0.35 - up * 0.3 - fwd * 0.2, hand_frame(fwd * 0.9 + lat * 0.1, 'L', I=up - lat * 0.1), FIST
        if pose_name == 'raise':
            w = S + lat * 0.22 + up * (-0.05) + fwd * 0.40
            return w, S + lat * 0.50 - up * 0.25 - fwd * 0.1, hand_frame(fwd * 0.8 + up * 0.3, 'L', I=up * 0.6 - fwd * 0.3 + lat * 0.2), FIST
        if pose_name == 'high':
            w = S + lat * 0.16 + up * 0.18 + fwd * 0.40
            return w, S + lat * 0.4 - up * 0.2, hand_frame(fwd * 0.8 + up * 0.3, 'L', I=up * 0.9 + lat * 0.3), FIST
        if pose_name in ('aim', 'aim_low', 'aim_near'):
            # the arrow line runs from the anchor under the RIGHT side of the chin to the target; the bow wrist sits on it
            # as far out as the left arm reaches (side-on stance: the torso keys turn her ~75 deg to her right)
            A = anchor()
            D = (TARGET - A).normalized()
            if pose_name == 'aim_low':
                D = (D - Vector((0, 0, 0.25))).normalized()
            reach = 0.47 if pose_name == 'aim_near' else 0.545
            t_hi, t_lo = 0.75, 0.05
            for _ in range(30):                                          # farthest point on the line within reach
                tm = (t_hi + t_lo) / 2
                if (A + D * tm - S).length > reach:
                    t_hi = tm
                else:
                    t_lo = tm
            w = A + D * t_lo
            upd = (Z_ - D * Z_.dot(D)).normalized()
            cant = Quaternion(D, math.radians(-12)) @ upd                     # bow top canted outward a little
            return w, S + lat * 0.45 - up * 0.25 - fwd * 0.05, hand_frame(D, 'L', I=cant), FIST    # elbow out, clear of the breast
    else:
        if pose_name == 'stand':
            waist = pbm('Spine1').translation
            w = waist - lat * 0.14 + fwd * 0.13 + up * 0.02
            return w, S - lat * 0.45 - up * 0.1 - fwd * 0.1, hand_frame(lat * 0.65 - up * 0.65 + fwd * 0.25, 'R', Zd=-fwd + lat * 0.2), RELAX
        if pose_name == 'lowerR':                                # recovery: the hand swings out round the breast to the hip
            w = S - lat * 0.24 - up * 0.30 + fwd * 0.20
            return w, S - lat * 0.45 - up * 0.15 - fwd * 0.15, ('dir', None, 0.0), RELAX
        if pose_name == 'lift':
            w = S - lat * 0.10 + up * (-0.05) + fwd * 0.25
            return w, S - lat * 0.40 + up * 0.0 + fwd * 0.10, ('dir', up * 0.9 + fwd * 0.3, 0.0), RELAX
        if pose_name == 'quiver':
            w = S - lat * 0.02 + up * 0.20 - fwd * 0.10
            return w, S - lat * 0.25 + up * 0.25 + fwd * 0.35, ('dir', up * 0.8 - fwd * 0.5 + lat * 0.1, 0.0), PINCH
        if pose_name == 'overhead':
            w = S + lat * 0.05 + up * 0.36 + fwd * 0.12
            return w, S - lat * 0.35 + up * 0.15 + fwd * 0.25, ('dir', up * 0.6 + fwd * 0.6 + lat * 0.2, 0.0), PINCH
        if pose_name == 'bring':
            Bw = bow_world(); R = Bw.to_3x3().normalized(); nk = Bw @ NOCK
            w = nk - (-R.col[0]) * 0.12 + R.col[1] * 0.10 - lat * 0.04
            return w, S - lat * 0.40 - fwd * 0.30 + up * 0.10, ('dir', -R.col[0] + R.col[1] * 0.5, 0.0), PINCH
        if pose_name in ('release', 'release2'):
            Bw = bow_world(); grip = Bw.translation; Dn = -Bw.to_3x3().col[0].normalized()
            A = anchor()                                                # follow-through: the open hand flicks back and out
            if pose_name == 'release':
                pt = A - Dn * 0.22 - lat * 0.22 - up * 0.02
            else:
                pt = A - Dn * 0.12 - lat * 0.30 - up * 0.14
            return pt, A - Dn * 0.6 + up * 0.1, ('dirf', Dn * 0.8 - lat * 0.6, 0.0), RELAX
    raise KeyError((side, pose_name))


def anchor():
    """full-draw anchor: under the right side of the chin, in the head frame"""
    M = pbm('Head'); R = M.to_3x3().normalized()
    return M.translation - R.col[0] * 0.065 + R.col[2] * 0.075 - Vector((0, 0, 0.045))


def string_target():
    """right wrist target putting the pinch on the (drawn) string; hand pointing at the bow, index up"""
    Bw = bow_world(); R = Bw.to_3x3().normalized()
    return R


def interp_keys(keys, t):
    for (ta, a), (tb, b) in zip(keys[:-1], keys[1:]):
        if ta <= t <= tb:
            return a, b, ss((t - ta) / (tb - ta)) if tb > ta else 1.0, (t - ta) / max(tb - ta, 1e-6)
    return keys[-1][1], keys[-1][1], 1.0, 1.0


def solve_spec(side, a, b, f, fl=None, wrist_override=None):
    wa, pa, ra, ca = arm_spec(side, a); wb, pb_, rb, cb_ = arm_spec(side, b)
    w = wa.lerp(wb, f); p = pa.lerp(pb_, f)
    q = ('mix', ra, rb, f)
    if wrist_override is not None:
        w = wrist_override
    arm(side, w, p, q, log=fl)
    curl(side, blend_curl(ca, cb_, f))


ATTACK_LOG = []


def attack(t, fl=None):
    reset()
    keys = attack_keys()
    a, b, f, _ = interp_keys(keys, t)
    g = lambda k: lerp(a[k], b[k], f)
    st = axial_stand(0.0, amp=0.0)
    twist = profile(g('col_turn'), NC)
    st['col_pitch'] = profile(math.radians(-g('lean') * 0.3), NC)
    apply_axial(curve(**st), twist)
    torso(lean=g('lean'), turn=g('turn'), head_yaw=-g('turn') * 0.6 + g('head'))
    if a['bowpose'].startswith('aim') or b['bowpose'].startswith('aim'):
        w_aim = ss((t - 0.45) / 0.15)
        look_at(TARGET, 0.75 * w_aim * (1 - ss((t - 1.12) / 0.38)))
    # bow arm
    solve_spec('L', a['bowpose'], b['bowpose'], f, fl)
    # string / right arm
    draw = a['draw'] if b['rpose'] == 'release' else g('draw')      # the hand leaves from full draw, not along the string
    Bw = bow_world(); R = Bw.to_3x3().normalized()
    on = g('rs')
    if a['rpose'] == 'string' or b['rpose'] == 'string':
        # pinch on the string at the current draw; approach from the previous pose
        if a['rpose'] == 'string' and b['rpose'] == 'string':
            fr = 1.0
        elif b['rpose'] == 'string':
            fr = f
        else:
            fr = 1.0 - f
        full = max(0.0, min(0.66, (Bw.inverted() @ anchor()).x - NOCK.x))  # braced string -> anchor along the bow's +X
        nock_w = Bw @ (NOCK + Vector((draw * full, 0, 0)))
        Dn = -R.col[0]; hr = ('dirf', Dn, 0.0)                    # knuckles toward the bow, roll left to the forearm
        lat, up, fwd = chest(); S = pbm('UpperArm_R').translation
        pole = nock_w - Dn * 0.65 + up * 0.08                         # elbow behind on the arrow line (forearm along it)
        other = a['rpose'] if a['rpose'] != 'string' else b['rpose']
        if other == 'string':
            wo, po, ro, co_ = nock_w - Dn * 0.17, pole, hr, HOOK
        else:
            wo, po, ro, co_ = arm_spec('R', other)
        # wrist so that the pinch lands on the nock: iterate on the measured pinch point
        wt = nock_w - Dn * 0.17
        for _ in range(3):
            PENDING['R'] = len(fl.get('R', [])) if fl is not None else 0
            arm('R', wo.lerp(wt, fr), po.lerp(pole, fr), ('mix', ro, hr, fr), clav=(0.02 * fr, -0.05 * fr))
            curl('R', blend_curl(co_, HOOK, fr))
            err = nock_w - pinch_point('R')
            wt = wt + err * 0.9
            reset_arm('R')
        arm('R', wo.lerp(wt, fr), po.lerp(pole, fr), ('mix', ro, hr, fr), clav=(0.02 * fr, -0.05 * fr), log=fl)
        curl('R', blend_curl(co_, HOOK, fr))
    else:
        solve_spec('R', a['rpose'], b['rpose'], f, fl)
    # string: follows the pinch while drawn, snaps back with a small overshoot after the release
    if on > 0.5 and (a['rpose'] == 'string' and b['rpose'] == 'string'):
        pn = pinch_point('R'); nb = Bw.inverted() @ pn; dr = max(0.0, nb.x - NOCK.x)
        set_string(dr)
    elif RELEASE <= t < RELEASE + 0.1:
        set_string(-0.012 * math.cos(2 * math.pi * (t - RELEASE) / 0.1) * (1 - (t - RELEASE) / 0.1))
    else:
        set_string(0.0)
    # arrow
    vis = (a['arrow'] > 0 or b['arrow'] > 0) and not (a['arrow'] == 0 and f < 0.5) and t < RELEASE
    if a['arrow'] == 0 and b['arrow'] == 1:
        vis = f >= 0.5
    if vis:
        Bw = bow_world(); rest_w = Bw @ REST_ARROW; sn = pbm('StringNock').translation
        nocked = (rest_w - sn).normalized(); bow_up = Bw.to_3x3().col[1].normalized()
        if a['arrow'] == 2 and b['arrow'] == 2 or (a['arrow'] == 2):
            set_arrow(sn, nocked, bow_up)
        else:
            pn = pinch_point('R'); lat, up, fwd = chest()
            qd = (-lat * 0.25 - fwd * 0.5 + up * 0.95).normalized()            # out of the quiver: up and back
            if b['arrow'] == 2:
                d = qd.lerp(nocked, ss(f)).normalized(); base = pn.lerp(sn, ss(f))
            elif a['rpose'] == 'quiver' and b['rpose'] == 'overhead':
                d = qd.lerp((up * 0.6 + fwd * 0.4).normalized(), ss(f)).normalized(); base = pn
            elif a['rpose'] == 'overhead' and b['rpose'] == 'bring':
                d = (up * 0.6 + fwd * 0.4).normalized().lerp(nocked, ss(f)).normalized(); base = pn
            elif a['rpose'] == 'overhead':
                d = (up * 0.6 + fwd * 0.4).normalized(); base = pn
            else:
                d = qd; base = pn
            # the arrow is held at its nock end: shaft forward of the pinch
            set_arrow(base, d, Z_ if abs(d.z) < 0.9 else fwd)
    else:
        set_arrow(None, None, None, visible=False)


def reset_arm(side):
    for n in [f'{x}_{side}' for x in ('Clavicle', 'UpperArm', 'ForeArm', 'ForeArmTwist', 'Hand')] + \
             [f'{fn}{k}_{side}' for fn in FINGERS for k in (1, 2, 3)]:
        rig.pose.bones[n].matrix_basis = Matrix()
    bpy.context.view_layer.update()


def hit(t, fl=None):
    reset()
    r = ss(t / 0.10) * (1 - ss((t - 0.22) / 0.5))
    st = axial_stand(0.0, amp=0.0)
    st['col_pitch'] = profile(-0.22 * r, NC, 1.3); st['col_yaw'] = profile(0.10 * r, NC)
    apply_axial(curve(**st), profile(0.12 * r, NC))
    torso(lean=-14 * r, turn=10 * r, side=-5 * r, head_pitch=-16 * r, head_yaw=8 * r, head_roll=6 * r)
    lat, up, fwd = chest()
    SL = pbm('UpperArm_L').translation; SR = pbm('UpperArm_R').translation
    wL, pL, rL, cL = arm_spec('L', 'stand')
    arm('L', wL + lat * 0.10 * r + up * 0.10 * r - fwd * 0.04 * r, pL, rL, log=fl); curl('L', FIST)
    wR, pR, rR, cR = arm_spec('R', 'stand')
    wR2 = SR - lat * 0.20 + up * 0.02 + fwd * 0.22
    arm('R', wR.lerp(wR2, r), pR, ('mix', rR, hand_frame(fwd * 0.5 - lat * 0.5 + up * 0.3, 'R', Zd=fwd), r), log=fl)
    curl('R', blend_curl(RELAX, OPEN, r))


def fidget(t, fl=None):
    T = 2.0; reset()
    e = ss(t / 0.4) * (1 - ss((t - 1.55) / 0.45))
    apply_axial(curve(**axial_stand(t, 2.625, 0.6)), profile(-0.05 * e, NC))
    look = math.sin(2 * math.pi * t / T)
    torso(lean=-2 * e, turn=-6 * e * look, head_yaw=35 * e * look, head_pitch=-6 * e, head_roll=4 * e * look)
    lat, up, fwd = chest()
    stand_arms(t, 0.0, fl, bow_up=0.9 * ss(t / 0.5) * (1 - ss((t - 1.4) / 0.5)))


DEATH_T = 1.5
BOW_DROP = {}


def death(t, fl=None):
    """native m282d*/xa0: she recoils, twists and topples to her LEFT; the column lies along the floor to her left, the
    torso continues it on her left side with the front toward the party, the bow arm thrown out past the head, the
    right arm across the body; the tail stays behind with a slack curve."""
    reset()
    u = min(t, DEATH_T)
    f1 = ss(u / 0.30) * (1 - ss((u - 0.3) / 0.4))      # recoil (lean back) early
    f2 = ss((u - 0.12) / 0.9)                          # the topple
    dirs = []
    for idx, i in enumerate(COL):
        lagw = idx / max(NC - 1, 1)
        g = ss((u - 0.12 - 0.22 * (1 - lagw)) / 0.85)
        flat = Vector((1.0, -0.25 - 0.15 * lagw, -0.02)).normalized()
        d = (Matrix.Rotation(-0.25 * f1, 3, 'X') @ Vector(REST_DIR[i])).lerp(flat, g).normalized()
        dirs.append(d)
    k, h0 = tail_straight(curl=0.0)
    k = k + 0.45 * f2 * np.sin(np.linspace(0, 2.0 * math.pi, len(k)))
    root = (0.0, 0.0, -(J0[K][2] - RAD[K]) * f2)
    P = curve(col_dirs=dirs, kappa=k, tail_heading=-0.15 * f2, root_offset=root, floor_top=0.23 * f2)
    apply_axial(P, profile(0.0, NC))
    torso(lean=-14 * f1 + 4 * f2, turn=8 * f2, side=-6 * f2, head_pitch=-20 * f1 - 8 * f2, head_yaw=-25 * f2, head_roll=10 * f2)
    lat, up, fwd = chest()
    SL = pbm('UpperArm_L').translation; SR = pbm('UpperArm_R').translation
    wL, pL, rL, cL = arm_spec('L', 'stand')
    # left arm out past the head along the floor (the torso's up axis now points along the floor to her left)
    wL2 = SL + up * 0.45 + fwd * 0.12; wL2.z = max(wL2.z, 0.10)
    wM = SL + lat * 0.42 + fwd * 0.22 - up * 0.05                  # flung out sideways on the way (keeps the elbow open)
    wL = (wL * (1 - f2) ** 2 + wM * 2 * f2 * (1 - f2) + wL2 * f2 * f2); wL.z = max(wL.z, 0.10)
    arm('L', wL, pL.lerp(SL + up * 0.2 - fwd * 0.3 + Vector((0, 0, 0.3)), f2), ('mix', rL, ('dir', None, 0.0), f2), log=fl)
    fd = ss((u - 0.40) / 0.40)                          # the bow slips from the fist and falls flat beside her
    curl('L', blend_curl(FIST, RELAX, fd))
    if fd > 0:
        bp = rig.pose.bones['Bow']
        if 'release' not in BOW_DROP:                           # the bow leaves the fist at u = 0.40: fall from there,
            BOW_DROP['release'] = None                          # independent of the hand
            keep = capture(); death(0.40); BOW_DROP['release'] = rig.pose.bones['Bow'].matrix.copy()
            for k, (q, l, sc_) in keep.items():
                pbk = rig.pose.bones[k]; pbk.rotation_quaternion = q; pbk.location = l; pbk.scale = sc_
            bpy.context.view_layer.update()
        Bin = BOW_DROP['release'] if BOW_DROP['release'] is not None else bp.matrix.copy()
        Bf = Matrix((Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)))).transposed().to_4x4()
        Bf.translation = Vector((1.05, -0.95, 0.03))
        pos = Bin.translation.lerp(Bf.translation, fd) + Vector((0, 0, 0.12 * math.sin(math.pi * fd)))
        rot = Bin.to_quaternion().slerp(Bf.to_quaternion(), fd)
        bp.matrix = Matrix.LocRotScale(pos, rot, Vector((1, 1, 1))); bpy.context.view_layer.update()
    wR, pR, rR, cR = arm_spec('R', 'stand')
    wR2 = SR + fwd * 0.30 + up * 0.10 - lat * 0.05; wR2.z = max(wR2.z, 0.08)
    wR = wR.lerp(wR2, f2)
    arm('R', wR, pR.lerp(SR - lat * 0.35 + fwd * 0.05, f2),
        ('mix', rR, hand_frame(fwd * 0.6 + up * 0.4, 'R', Zd=Vector((0, 0, -1))), f2), log=fl)
    curl('R', blend_curl(RELAX, OPEN, f2))


# ================================================================== hair snakes
HAIRJ = json.load(open(W('hair.json')))
for h in HAIRJ:
    h['hang'] = (h['pts'][0][2] - h['pts'][-1][2]) > 0.15
REST_ROT = {pb.name: pb.bone.matrix_local.to_3x3().to_quaternion() for pb in rig.pose.bones}
CLIP_T = {'T': 2.0}


def world_delta(n):
    return pbm(n).to_3x3().to_quaternion() @ REST_ROT[n].inverted()


def hair_pose(t, writhe=1.0, floor=0.035):
    """hanging snakes partly follow the chest (gravity), every snake writhes slowly, and no bone end goes under the floor"""
    Dh, Dc = world_delta('Head'), world_delta('Spine2')
    T = CLIP_T['T']; ncyc = max(1, round(T / 1.3))
    for h in HAIRJ:
        k = h['k']
        for j, follow, amp in ((1, 0.45, 5.0), (2, 0.75, 9.0)):
            n = f'Hair_{k:02d}_{j}'; pb = rig.pose.bones[n]
            if h['hang']:
                D = Dh.slerp(Dc, follow)
                M = Matrix.LocRotScale(pb.head.copy(), (D @ REST_ROT[n]), Vector((1, 1, 1)))
                pb.matrix = M; bpy.context.view_layer.update()
            ph = 2 * math.pi * (ncyc * t / T) + 1.7 * k + 0.9 * j
            a = math.radians(amp * writhe * math.sin(ph))
            if abs(a) > 1e-5:
                ax = (pb.tail - pb.head).normalized().cross(Vector((0.3, 0.2, 1)).normalized() if k % 2 else Vector((1, 0, 0.2)).normalized())
                if ax.length > 1e-6:
                    PO.rotate_world(rig, n, ax.normalized(), math.degrees(a))
            hd, tl = pb.head.copy(), pb.tail.copy()
            if tl.z < floor:
                d = tl - hd; L = d.length
                hz = max(hd.z, floor) - hd.z
                flat = Vector((d.x, d.y, 0)).normalized() if Vector((d.x, d.y)).length > 1e-6 else Vector((1, 0, 0))
                want = flat * (L * L - hz * hz) ** 0.5 + Vector((0, 0, hz)) if L > hz else Vector((0, 0, L))
                PO.aim_bone(rig, n, hd + want)


# ================================================================== keying
def capture():
    return {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}


HAIR_CHAIN_IDS = {}


def hair_ground(iters=12, step=7.0):
    """mesh floor rule for the snakes: lift every chain whose vertices go under the floor (rotate its first bone up
    about its head, then its second), re-measuring the evaluated mesh each pass"""
    body = bpy.data.objects['Body']
    if not HAIR_CHAIN_IDS:
        HAIR_CHAIN_IDS.update({h['k']: np.where(_pv == h['piece'])[0] for h in HAIRJ})
    for _ in range(iters):
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
        z = np.array([v.co.z for v in m.vertices]); ev.to_mesh_clear()
        moved = False
        for h in HAIRJ:
            if z[HAIR_CHAIN_IDS[h['k']]].min() < 0.005:
                for j in (1, 2):
                    n = f'Hair_{h["k"]:02d}_{j}'; pb = rig.pose.bones[n]
                    d = (pb.tail - pb.head).normalized(); ax = d.cross(Vector((0, 0, 1)))
                    if ax.length > 1e-4:
                        PO.rotate_world(rig, n, ax.normalized(), step)
                moved = True
        if not moved:
            break


def hair_low():
    body = bpy.data.objects['Body']
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
    z = np.array([v.co.z for v in m.vertices]); ev.to_mesh_clear()
    return float(z[HAIR_MASK].min())


def ground_lift(name, t):
    """corpse rule: lift the pelvis so no upper-body vertex goes below the floor (measured on the evaluated mesh)"""
    body = bpy.data.objects['Body']
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
    z = np.array([v.co.z for v in m.vertices]); ev.to_mesh_clear()
    up = UPPER_MASK
    low = float(z[up].min()); HAIR_LOW.append(float(z[HAIR_MASK].min()))
    if low < 0.005:
        pb = rig.pose.bones['Pelvis']; M = pb.matrix.copy(); M.translation.z += 0.005 - low
        pb.matrix = M; bpy.context.view_layer.update()
    return low


bodyme = bpy.data.objects['Body'].data
_co = np.array([tuple(v.co) for v in bodyme.vertices])
_pv = np.zeros(len(_co), np.int32); bodyme.attributes['piece'].data.foreach_get('value', _pv)
HAIR_PIECES = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 23, 24, 35]
HAIR_MASK = np.isin(_pv, HAIR_PIECES)
UPPER_MASK = (_co[:, 2] > 0.95) & ~HAIR_MASK


def key_action(name, seconds, loop, fn, ground=False):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    n = int(round(seconds * FPS)); poses = []; fl = {}; lows = []
    PREV_TW.clear(); PREV_IK.clear(); PLAN.clear(); CHOSEN.clear(); PLAN_TW.clear()
    MODE['m'] = 'plan'; flp = {}
    for fr in range(n + 1):
        fn((fr % n) / FPS if loop else fr / FPS, flp)
    plan_swivels(); MODE['m'] = 'final'; PREV_TW.clear()
    CLIP_T['T'] = seconds if loop else 2.6
    for fr in range(n + 1):
        t = (fr % n) / FPS if loop else fr / FPS
        fn(t, fl)
        if ground:
            lows.append(ground_lift(name, t))
        hair_pose(t if name != 'Dead' else DEATH_T, writhe=0.0 if name == 'Dead' else 1.0)
        if ground:
            hair_ground()
            HAIR_LOW[-1] = hair_low()
        poses.append(capture())
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for fr, pose in enumerate(poses):
        for k, (q, l, s) in pose.items():
            if k in prev and prev[k].dot(q) < 0:
                q = -q
            prev[k] = q
            pb = rig.pose.bones[k]; pb.rotation_quaternion = q; pb.location = l; pb.scale = s
            pb.keyframe_insert('rotation_quaternion', frame=fr); pb.keyframe_insert('location', frame=fr)
            if k == 'Arrow':
                pb.keyframe_insert('scale', frame=fr)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    tw = {s: [x[0] for x in v] for s, v in fl.items()}; sw = {s: [x[1] for x in v] for s, v in fl.items()}
    ARMLOG[name] = {s: {'twist_min': min(tw[s]), 'twist_max': max(tw[s]), 'swing_max': max(sw[s]),
                        'twist_step_max': max(abs(a - b) for a, b in zip(tw[s][1:], tw[s][:-1])) if len(tw[s]) > 1 else 0,
                        'per_frame': fl[s]}
                    for s in tw}
    print('CLIP', name, seconds, 'frames', n + 1, 'arms', json.dumps({k: {a: b for a, b in v.items() if a != 'per_frame'} for k, v in ARMLOG[name].items()}),
          ('corpse low %.3f hair low %.3f' % (min(lows), min(HAIR_LOW))) if lows else '', flush=True)
    HAIR_LOW.clear()
    return act


def keep_dead(t, fl=None):
    death(DEATH_T, fl)


CLIPS = [('Standing', 2.625, True, standing, False), ('Walking', 0.875, True, lambda t, fl=None: gait(t, 0.875, STRIDE_WALK, 2.2, 0.03, log=fl), False),
         ('Running', 0.7, True, lambda t, fl=None: gait(t, 0.7, STRIDE_RUN, 2.8, 0.10, run=True, log=fl), False),
         ('Attack', 1.5, False, attack, False), ('Hit', 0.75, False, hit, False), ('Fidget', 2.0, False, fidget, False),
         ('Death', DEATH_T, False, death, True), ('Dead', 1.0, False, keep_dead, True)]
only = os.environ.get('CLIPS')
for name, sec, loop, fn, ground in CLIPS:
    if only and name not in only.split(','):
        continue
    key_action(name, sec, loop, fn, ground)
json.dump({'fps': FPS, 'walk_stride_m': STRIDE_WALK, 'run_stride_m': STRIDE_RUN, 'attack_impact_s': IMPACT,
           'durations': {c[0]: c[1] for c in CLIPS}, 'arms': ARMLOG}, open(W('clips.json'), 'w'), indent=1)
reset()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('SAVED', out)
