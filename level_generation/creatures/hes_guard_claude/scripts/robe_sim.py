"""Bake the cloak chains (cloak_rig.py) into every clip (druidess; adapted from mm6_thf_claude/scripts/cloak_sim.py).
Args: -- <in blend> <out blend> [clip ...]

Per chain point (8 below each root: joints and bone midpoints, 15 chains): verlet with velocity damping DAMP per
substep (SUB substeps per 30 fps frame); a pull (STIFF per substep) toward the rest bell hung from the chain root with
the chest's heading only (yaw), so the cloak hangs plumb when the body leans, blending into the chest's own frame as
the chest tilts past 25-70 deg. Lying (death): SUPINE (chest forward up) flattens the target onto the floor (the
cloak spreads under her); PRONE (chest forward down: her death kneels and lies face down) keeps the chest-frame target
over her back and lowers it by DRAPE toward the floor, and collisions then push radially out of the capsules, so the
cloth settles over the body (the native corpse: prone under the spread cloak). Exact segment lengths; neighbour chains
kept between 0.6 and NB_MAX x their rest spacing; collisions last in each of 3 constraint iterations; one-sided
collision capsules while upright (a point inside moves outward along its chain's direction: thief, the back leg swept
points inside the cloak), radial when lying; floor z >= FLOOR. Chain roots ride on B_Spine2. Loops (Standing,
Walking, Fidget) simulate three cycles and keep the last (seamless); one-shots pre-roll PRE frames on their first
pose; Death settles SETTLE frames more (written into Dead by the export, which holds Death's last frame).
Each chain bone is then aimed at the next simulated point and keyed (quaternion) on every clip frame."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[0], args[1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; scene.render.fps = 30; scene.render.fps_base = 1
arm = bpy.data.objects['Rig']
CH = json.loads(scene[os.environ.get('CHAINS_KEY', 'cloak_chains')])
CHEST = os.environ.get('ROOT', 'B_Pelvis')
PREFIX = os.environ.get('PREFIX', 'Robe_')     # banners: CHAINS_KEY=banner_chains ROOT=B_Spine2 PREFIX=Banner_
SUB, DAMP, STIFF, MARGIN, FLOOR, PRE, SETTLE, DRAPE = 5, 0.94, 0.09, float(os.environ.get('MARGIN', '0.012')), 0.025, 24, 30, 0.35
# user review 1 (2026-10-11): "cloak flapping erratically" in every action. Measured (motion_probe.py): even Standing
# jittered (jerk p95 5 cm/frame^2, ~23 velocity reversals per point in 2 s); hit 58, death 89 cm/frame^2 peaks. Damping
# 0.985 -> 0.94 per substep and the pull 0.05 -> 0.09 make the cloth follow the body instead of ringing, and the kept
# trajectories are smoothed over time (Gaussian SMOOTH_SIG frames; circular for loops)
SMOOTH_SIG = float(os.environ.get('CLOAK_SMOOTH', '1.5'))
PUSH_CAP = 0.004
DROP_FLAT = bool(os.environ.get('DROP_FLAT'))
NB_MAX = 1.06
LOOPS = {'Standing', 'Walking', 'Running', 'Fidget'}
CLIPS = args[2:] or [n for n in ('Standing', 'Walking', 'Attack', 'Cast', 'Hit', 'Death', 'Fidget')
                     if n in bpy.data.actions]
order = sorted(range(len(CH)), key=lambda i: CH[i]['deg'])
REST = []
for c in CH:
    J = np.array(c['pts']); F = []; nbn = len(c['bones'])
    for k in range(nbn):
        F += [J[k], (J[k] + J[k + 1]) / 2]
    F.append(J[nbn]); REST.append(np.array(F))
NP = len(REST[0])
OUT = [np.array([math.sin(math.radians(c['deg'])), math.cos(math.radians(c['deg'])), 0.0]) for c in CH]
# the native cloak hangs close round the legs; the rest bell is the A-pose cloak (Meshy flared it to clear the spread
# arms) and read far too wide in game next to the sprites: the hanging target's horizontal offset from each chain root
# shrinks toward the hem by up to NARROW (the leg capsules keep it off the body)
NARROW = float(os.environ.get('CLOAK_NARROW', '0.0'))
for c in range(len(REST)):
    off = REST[c] - REST[c][0]
    f = 1 - NARROW * np.linspace(0, 1, len(off))[:, None]
    off[:, :2] *= f
    REST[c] = REST[c][0] + off
STEPS = np.arange(0.0, 0.45, 0.004)
# Moon Cleric (mm7 batch B): the legs have no geometry under the floor-length robe, so the capsules only have to move
# the cloth plausibly; m460's wide leg/heel capsules (0.085-0.12 m) bulged the closed A-line robe at the hips and
# knees in Standing and kicked the back hem out into a train in the walk. Radii as LEG_R x the values below.
LEG_R = float(os.environ.get('LEG_R', '1.0'))
FINGER_TIP = float(os.environ.get('FINGER_TIP', '0.17'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
# legless robes: leg capsules only move the cloth (0.035 floor); visible legs (the mage keeps his) need their radius
LEG_FLOOR = float(cfg.C.get('leg_capsule_floor', 0.035))
CAPS = [('B_L_Thigh', 'B_L_Calf', 0.065 * LEG_R), ('B_R_Thigh', 'B_R_Calf', 0.065 * LEG_R), ('B_L_Calf', 'B_L_Foot', 0.05 * LEG_R),
        ('B_R_Calf', 'B_R_Foot', 0.05 * LEG_R), ('B_L_Thigh', 'B_R_Thigh', 0.07 * LEG_R), ('B_Spine', 'B_Spine2', 0.12),
        ('B_Spine2', 'B_Neck', 0.10),
        ('B_L_UpperArm', 'B_L_Forearm', 0.05), ('B_R_UpperArm', 'B_R_Forearm', 0.05),
        ('B_L_Forearm', 'B_L_Hand', 0.045), ('B_R_Forearm', 'B_R_Hand', 0.045),
        ('B_L_Foot', 'B_L_Toe0', 0.05 * LEG_R), ('B_R_Foot', 'B_R_Toe0', 0.05 * LEG_R),
        ('B_L_Hand', 'B_L_Hand:tip', 0.045), ('B_R_Hand', 'B_R_Hand:tip', 0.045)]   # the long claws (cast reached into a banner)
# legs: the cloth between two chains is interpolated, so a leg between chains poked through at shin height in the walk
# with radii 0.09/0.075 (each chain point cleared it); wider leg capsules keep the neighbouring chains further off
# heel points (the walking heels bulged through the back hem: the shin capsules end at the ankle joint): behind and
# below the ankle, opposite the toe direction


def joint(n, pose=True):
    if n.endswith(':tip'):                         # 70 % of the way to the middle fingertip (FINGER_TIP m past the wrist)
        h = n.split(':')[0]; hp = joint(h, pose)
        mk = joint(h.replace('Hand', 'Finger2'), pose)
        d = (mk - hp) / max(np.linalg.norm(mk - hp), 1e-9)
        return hp + d * 0.7 * FINGER_TIP
    if n.endswith(':heel'):
        f = n.split(':')[0]; t = f.replace('Foot', 'Toe0')
        fh, th = joint(f, pose), joint(t, pose)
        return fh - 0.35 * (th - fh) + np.array([0.0, 0.0, -0.05])
    if pose:
        return np.array(arm.matrix_world @ arm.pose.bones[n].head)
    return np.array(arm.matrix_world @ arm.data.bones[n].head_local)


def set_action(act):
    arm.animation_data_create(); arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]


def strip_cloak(act):
    for l in getattr(act, 'layers', []):
        for s in l.strips:
            for cb in s.channelbags:
                for fc in list(cb.fcurves):
                    if f'"{PREFIX}' in fc.data_path:
                        cb.fcurves.remove(fc)
    if hasattr(act, 'fcurves'):
        for fc in list(act.fcurves):
            if f'"{PREFIX}' in fc.data_path:
                act.fcurves.remove(fc)


def body_state(t):
    scene.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
    sp = (arm.matrix_world @ arm.pose.bones[CHEST].matrix).copy()
    caps = [(joint(a), joint(b)) for a, b, r in CAPS]
    return sp, caps


rest_sp = arm.matrix_world @ arm.data.bones[CHEST].matrix_local
rest_caps = [(joint(a, False), joint(b, False)) for a, b, r in CAPS]


def seg_dist(p, a, b):
    ab = b - a; t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    q = a + np.outer(t, ab) if p.ndim == 2 else a + t * ab
    return p - q


radii = []
allrest = np.vstack([r[1:] for r in REST])
for (a, b), (na, _, r) in zip(rest_caps, CAPS):
    d = np.linalg.norm(seg_dist(allrest, a, b), axis=1).min()
    floor_r = 0.04 if ('Arm' in na or 'Forearm' in na) else (LEG_FLOOR if any(t in na for t in ('Calf', 'Thigh', 'Foot')) else 0.10)
    radii.append(min(r, max(floor_r, d - MARGIN - 0.004)))
print('CAPSULE radii', [round(x, 3) for x in radii])


def yaw_rot(sp):
    f = sp.to_3x3() @ rest_sp.to_3x3().inverted() @ Vector((0, -1, 0))
    a = math.atan2(f.x, -f.y)
    return np.array(Matrix.Rotation(a, 3, 'Z'))


def tilt(sp):
    """(weight 0 upright .. 1 lying, prone?)"""
    R = sp.to_3x3() @ rest_sp.to_3x3().inverted()
    up = R @ Vector((0, 0, 1)); fwd = R @ Vector((0, -1, 0))
    t = math.degrees(up.angle(Vector((0, 0, 1))))
    x = min(1.0, max(0.0, (t - 25.0) / 45.0))
    return x * x * (3 - 2 * x), fwd.z < 0


def roots(sp):
    M = sp @ rest_sp.inverted()
    return [np.array(M @ Vector(r[0])) for r in REST]


SEGLEN = [np.linalg.norm(np.diff(r, axis=0), axis=1) for r in REST]


def rigid_floor(x, seg):
    """Straight rigid bones (joint to joint = bone length, midpoint on the line) from the root down; a bone that would
    dip under the floor slides along it instead."""
    for k in range(0, NP - 1, 2):
        d = x[k + 2] - x[k]; L = np.linalg.norm(d); Lb = seg[k] + seg[k + 1]
        x[k + 2] = x[k] + d / max(L, 1e-9) * Lb
        if x[k + 2][2] < FLOOR:
            dz = FLOOR - x[k][2]
            if abs(dz) < Lb:
                hor = d.copy(); hor[2] = 0; hn = np.linalg.norm(hor)
                hor = hor / hn if hn > 1e-9 else np.array([0.0, 1.0, 0.0])
                x[k + 2] = x[k] + hor * math.sqrt(Lb * Lb - dz * dz) + np.array([0, 0, dz])
            else:
                x[k + 2][2] = FLOOR
        x[k + 1] = (x[k] + x[k + 2]) / 2


def simulate(act, mode):
    stiff = STIFF * (2.5 if act.name == 'Death' else 1.0)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    n = f1 - f0
    if mode == 'loop':
        times = [f0 + (i % n) for i in range(3 * n)] + [f1]
        keep_from = 2 * n
    else:
        times = [f0] * PRE + list(range(f0, f1 + 1)) + ([f1] * SETTLE if mode == 'settle' else [])
        keep_from = PRE
    sp, caps = body_state(times[0])
    R0 = roots(sp); Ry = yaw_rot(sp)
    X = [np.array([R0[c] + Ry @ (REST[c][k] - REST[c][0]) for k in range(NP)]) for c in range(len(CH))]
    V = [np.zeros_like(x) for x in X]
    seglen = [np.linalg.norm(np.diff(r, axis=0), axis=1) for r in REST]
    if 'group' in CH[0]:                           # open sheets (banners): neighbours inside each sheet, no wrap
        nb = [(i, i + 1) for i in range(len(CH) - 1) if CH[i]['group'] == CH[i + 1]['group']]
    else:
        nb = [(order[i], order[(i + 1) % len(order)]) for i in range(len(order))]
    nbrest = {(a, b): np.linalg.norm(REST[a][1:] - REST[b][1:], axis=1) for a, b in nb}
    prev = (sp, caps)
    res = []
    for step, t in enumerate(times):
        cur = body_state(t)
        for s in range(SUB):
            w = (s + 1) / SUB
            M0, M1 = prev[0], cur[0]
            q = M0.to_quaternion().slerp(M1.to_quaternion(), w); tr = M0.translation.lerp(M1.translation, w)
            sp = Matrix.Translation(tr) @ q.to_matrix().to_4x4()
            caps = [(a0 + (a1 - a0) * w, b0 + (b1 - b0) * w) for (a0, b0), (a1, b1) in zip(prev[1], cur[1])]
            Rr = roots(sp); Ry = yaw_rot(sp); tw, prone = tilt(sp)
            if act.name != 'Death':
                tw = 0.0                                  # the hit's forward bend lifted the cloak in the chest frame
            Mc = sp @ rest_sp.inverted()
            old = [x.copy() for x in X]
            for c in range(len(CH)):
                x = X[c]
                tgt = np.array([Rr[c] + Ry @ (REST[c][k] - REST[c][0]) for k in range(NP)])
                if tw > 0:
                    tc = np.array([tuple(Mc @ Vector(REST[c][k])) for k in range(NP)])
                    tc[1:, 2] = np.maximum(tc[1:, 2] - 0.015, FLOOR)
                    if DROP_FLAT:                         # banners: lying, the cloth falls off the rods onto the floor
                        tc[1:, 2] = tc[1:, 2] * (1 - tw) + (FLOOR + 0.01) * tw
                    tgt = tgt * (1 - tw) + tc * tw
                x[1:] += V[c][1:] * DAMP + (tgt[1:] - x[1:]) * stiff
                x[0] = Rr[c]
            for it in range(3):
                for c in range(len(CH)):
                    x = X[c]
                    for k in range(0, NP - 1, 2):         # rigid straight bones: joint to joint, midpoint on the line
                        d = x[k + 2] - x[k]; L = np.linalg.norm(d)
                        Lb = seglen[c][k] + seglen[c][k + 1]
                        x[k + 2] = x[k] + d / max(L, 1e-9) * Lb
                        x[k + 1] = (x[k] + x[k + 2]) / 2
                for a, b in nb:
                    d = X[b][1:] - X[a][1:]; L = np.linalg.norm(d, axis=1); r = nbrest[(a, b)]
                    corr = np.where(L > NB_MAX * r, L - NB_MAX * r, np.where(L < 0.6 * r, L - 0.6 * r, 0.0))
                    u = d / np.maximum(L, 1e-9)[:, None]
                    X[a][1:] += u * (corr * 0.5)[:, None]; X[b][1:] -= u * (corr * 0.5)[:, None]
                for c in range(len(CH)):
                    x = X[c]; u0 = Ry @ OUT[c]
                    for (a, b), r in zip(caps, radii):
                        d = seg_dist(x[1:], a, b); L = np.linalg.norm(d, axis=1)
                        for j in np.where(L < r + MARGIN)[0]:
                            q = x[1 + j]
                            if tw > 0.5 or act.name == 'Death':   # lying / falling: radial push (the kneeling legs fold back under the cloak)
                                dj = d[j] / max(L[j], 1e-9)
                                # capped per step: the knee striking the hem as she drops snapped it (40 cm/frame^2)
                                x[1 + j] = q + dj * min(r + MARGIN - L[j], PUSH_CAP)
                                continue
                            for st in STEPS:
                                if np.linalg.norm(seg_dist(q + u0 * st, a, b)) >= r + MARGIN:
                                    break
                            x[1 + j] = q + u0 * st
                    x[1:, 2] = np.maximum(x[1:, 2], FLOOR)
            for c in range(len(CH)):                      # final straight-bone pass (the floor moved joints)
                rigid_floor(X[c], seglen[c])
            for c in range(len(CH)):
                V[c] = X[c] - old[c]
        prev = cur
        if step >= keep_from:
            res.append((t, [x.copy() for x in X], cur[0].copy()))
    return res


AWI = arm.matrix_world.inverted()
L_rest = {}
for c in CH:
    par = CHEST
    for b in c['bones']:
        L_rest[b] = arm.data.bones[par].matrix_local.inverted() @ arm.data.bones[b].matrix_local
        par = b


previous_orientation = {}

def key_frame(frame, X, sp):
    """Each bone aims at the simulated joint below it; the simulation keeps every bone straight and rigid (joint
    distance = bone length), so the tails land exactly on the simulated joints (review 1: bones that aimed at folded
    half-segments overshot and the hem punched 15 cm through the floor, then snapped back)."""
    sp = AWI @ sp
    for c, x in zip(CH, X):
        Mp = sp
        for k, b in enumerate(c['bones']):
            Mu = Mp @ L_rest[b]
            basis = previous_orientation.get(b, Mu.to_3x3())
            y = basis @ Vector((0, 1, 0)); d = Vector(AWI @ Vector(x[2 * k + 2])) - Mu.translation
            R = y.rotation_difference(d.normalized()).to_matrix()
            basis = R @ basis
            previous_orientation[b] = basis.copy()
            Md = basis.to_4x4(); Md.translation = Mu.translation
            pb = arm.pose.bones[b]; pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = (Mu.inverted() @ Md).to_quaternion()
            pb.keyframe_insert('rotation_quaternion', frame=frame)
            Mp = Md

for name in CLIPS:
    act = bpy.data.actions[name]
    strip_cloak(act); set_action(act)
    for c in CH:
        for b in c['bones']:
            arm.pose.bones[b].rotation_mode = 'QUATERNION'; arm.pose.bones[b].rotation_quaternion = Quaternion()
    mode = 'loop' if name in LOOPS else ('settle' if name == 'Death' else 'once')
    res = simulate(act, mode)
    sig = SMOOTH_SIG * (2.0 if name == 'Death' else 1.0)   # the fall's knee contact kicked the outer hem (39 cm/frame^2)
    if sig > 0 and len(res) > 3:
        Xs = np.array([np.array(X) for _, X, _ in res])            # frames x chains x points x 3
        r_ = int(math.ceil(3 * sig)); kern = np.exp(-0.5 * (np.arange(-r_, r_ + 1) / sig) ** 2); kern /= kern.sum()
        n_ = len(Xs)
        idx = (np.arange(n_)[:, None] + np.arange(-r_, r_ + 1)[None, :])
        idx = idx % (n_ - 1) if mode == 'loop' else np.clip(idx, 0, n_ - 1)   # loops: the last frame closes the cycle
        Xsm = np.tensordot(kern, Xs[idx.T], axes=(0, 0)) if False else (Xs[idx] * kern[None, :, None, None, None]).sum(1)
        Xsm[:, :, 0] = Xs[:, :, 0]                                 # roots ride the chest exactly
        for i in range(len(Xsm)):                                  # smoothing shortened the bones: rigid + floor again
            for c in range(len(CH)):
                rigid_floor(Xsm[i, c], SEGLEN[c])
        res = [(t, [x for x in Xsm[i]], sp) for i, (t, _, sp) in enumerate(res)]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    frames = {}
    for t, X, sp in res:
        frames.setdefault(int(t), (X, sp))
    if mode == 'loop':
        frames = {int(t): (X, sp) for t, X, sp in res}
    if mode == 'settle':                                  # the last frame takes the settled state (Dead holds it)
        frames[f1] = (res[-1][1], res[-1][2])
    previous_orientation.clear()
    for f in range(f0, f1 + 1):
        X, sp = frames[f]
        key_frame(f, X, sp)
    disp = max(float(np.linalg.norm(frames[f1][0][c][1:] - REST[c][1:], axis=1).max()) for c in range(len(CH)))
    print('CLOAK', name, mode, 'frames', f1 - f0 + 1, 'max displacement at the last frame', round(disp, 3))
set_action(bpy.data.actions['Standing'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
