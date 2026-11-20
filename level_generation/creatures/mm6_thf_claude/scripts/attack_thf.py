"""Attack (melee and thrown dagger, 0.75 s, 18 frames at 24 fps) for the thief, into work/rig_v2.blend (after
build_clips_thf.py): two thrusts with alternating hands (the native keys alternate the hands; their raise-and-lower
read as showing off the knives, user review):
  0 rest; 0-2 the fists close (fist_solve.py curl) and the daggers appear (bone scale);
  3 the right hand chambers by the hip (elbow back, blade forward); 5 right thrust at chest height, arm extended,
  chest turned into it; 7 the right recoils to guard while the left chambers; 9 left thrust; 11 both in guard, held
  to 15; 15-18 back to rest, daggers vanish, hands open.
Arms: two-bone IK per frame to wrist targets on a Catmull-Rom spline through the keys, elbow pole per key. Hands: per
key the forearm roll (<= 50 deg, its change from the previous key penalised) and a wrist swing without twist
(<= 40 deg) that aim the blade (hammer grip at 55 deg to the forearm, seat_daggers.py), with a continuity cost to the
previous key's wrist rotation; between keys roll and wrist rotation are interpolated. The intent per key is written to
work/attack_intent.json; trace_gate.py compares the played clip with it. Chest: turns into each thrust and leans in.
Body (2026-10-14): a lunge, the right foot steps forward on the first thrust and back at the end, hips forward and
down into each thrust (leg IK, flat feet); the wrists ride the hip travel. The rest pose is blended in at frames 0-2
and 16-18 (legs by the size of the body motion)."""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Quaternion, Matrix, Euler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
scene = bpy.context.scene
scene.render.fps = 24
arm = bpy.data.objects['Thief_Rig']; mesh = bpy.data.objects['Thief']
arm.animation_data_create()
BONES = [pb.name for pb in arm.pose.bones]
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'


def set_action(act):
    arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]


def sample(act, t):
    """Pose {bone: (loc, quat)} of an action at a (fractional) frame."""
    set_action(act)
    scene.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
    return {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy().normalized()) for pb in arm.pose.bones}


def mix(a, b, w):
    out = {}
    for n in BONES:
        la, qa = a[n]; lb, qb = b[n]
        if qa.dot(qb) < 0:
            qb = -qb
        out[n] = (la.lerp(lb, w), qa.slerp(qb, w))
    return out


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def live(pose):
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location, pb.rotation_quaternion = pose[pb.name]
    bpy.context.view_layer.update()


def capture():
    return {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy().normalized()) for pb in arm.pose.bones}


def turn(bone, R):
    """Rotate a bone (and its children) by the world rotation matrix R about its head."""
    pb = arm.pose.bones[bone]
    M = arm.matrix_world @ pb.matrix; h = M.translation.copy()
    pb.matrix = arm.matrix_world.inverted() @ (Matrix.Translation(h) @ R.to_4x4() @ Matrix.Translation(-h) @ M)
    bpy.context.view_layer.update()


def world_turns(pose, turns):
    """Pose with bones turned about world axes through their heads: turns = [(bone, axis, degrees)] in order."""
    live(pose)
    for bone, axis, deg in turns:
        turn(bone, Matrix.Rotation(math.radians(deg), 3, Vector(axis)))
    return capture()


def aim(bone, tip, d):
    """Rotate `bone` about its head so the direction to the head of `tip` becomes d (world)."""
    a = arm.matrix_world @ arm.pose.bones[bone].head; b = arm.matrix_world @ arm.pose.bones[tip].head
    turn(bone, (b - a).normalized().rotation_difference(d.normalized()).to_matrix())


def curve(keys, f):
    """Smoothstep interpolation through [(frame, value), ...]."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * ease((f - f0) / (f1 - f0))
    return keys[-1][1]


def leg_ik(side, target, foot_world):
    """Two-bone leg IK: knee in the plane of the hip, the ankle target and a forward pole; the foot keeps the
    world orientation foot_world (flat on the floor)."""
    H = arm.matrix_world @ arm.pose.bones[side + 'UpLeg'].head
    l1, l2 = LEG[side]
    v = target - H; d = min(v.length, (l1 + l2) * 0.999); u = v.normalized()
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d); h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    pole = Vector((0, -1, 0)); pole = (pole - u * pole.dot(u)).normalized()
    K = H + u * a + pole * h
    aim(side + 'UpLeg', side + 'Leg', K - H)
    aim(side + 'Leg', side + 'Foot', (H + u * d) - K)
    pb = arm.pose.bones[side + 'Foot']
    M = foot_world.to_4x4(); M.translation = arm.matrix_world @ pb.head
    pb.matrix = arm.matrix_world.inverted() @ M
    bpy.context.view_layer.update()


def body_motion(pose, hips_fwd, hips_down, lean, step=0.0, lift=0.0):
    """Weight shift on a planted-leg pose: hips moved forward (-Y) and down, the chest leaned forward (deg, about +X
    through Spine02), the right foot stepped forward and lifted; legs solved by leg_ik with flat feet."""
    live(pose)
    pb = arm.pose.bones['Hips']
    M = arm.matrix_world @ pb.matrix
    M = Matrix.Translation(Vector((0, -hips_fwd, -hips_down))) @ M
    pb.matrix = arm.matrix_world.inverted() @ M
    bpy.context.view_layer.update()
    turn('Spine02', Matrix.Rotation(math.radians(lean), 3, Vector((1, 0, 0))))
    for side in ('Left', 'Right'):
        t = ANKLE[side] + (Vector((0, -step, lift)) if side == 'Right' else Vector())
        leg_ik(side, t, FOOT[side])
    return capture()


DAGGERS = ('DaggerL', 'DaggerR')
HIDDEN = Vector((0.001, 0.001, 0.001))


def write(name, poses, dagger_scale=None):
    """dagger_scale: per-frame scale of the dagger bones (default hidden: the daggers show only in the attack)."""
    if name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[name])
    act = bpy.data.actions.new(name); act.use_fake_user = True
    set_action(act)
    prev = {}
    for f, pose in enumerate(poses):
        for pb in arm.pose.bones:
            loc, q = pose[pb.name]
            if pb.name in prev and prev[pb.name].dot(q) < 0:       # no sign flips between keys
                q = -q
            prev[pb.name] = q
            pb.location, pb.rotation_quaternion = loc, q
            pb.keyframe_insert('location', frame=f)
            pb.keyframe_insert('rotation_quaternion', frame=f)
        for d in DAGGERS:
            s = HIDDEN if dagger_scale is None else Vector([max(dagger_scale[f], 0.001)] * 3)
            arm.pose.bones[d].scale = s
            arm.pose.bones[d].keyframe_insert('scale', frame=f)
    print('CLIP', name, 'frames 0 ..', len(poses) - 1, '(%.3f s)' % ((len(poses) - 1) / 24))
    return act


A = bpy.data.actions
rest = sample(A['Standing'], 0)
FIST = json.loads(scene['thf_fist']); SEAT = json.loads(scene['thf_daggers'])
# leg IK data from the Standing pose: ankle positions and flat foot orientations (world), leg segment lengths
live(rest)
ANKLE = {s_: (arm.matrix_world @ arm.pose.bones[s_ + 'Foot'].head).copy() for s_ in ('Left', 'Right')}
FOOT = {s_: (arm.matrix_world @ arm.pose.bones[s_ + 'Foot'].matrix).to_3x3().normalized() for s_ in ('Left', 'Right')}
LEG = {s_: ((arm.data.bones[s_ + 'Leg'].head_local - arm.data.bones[s_ + 'UpLeg'].head_local).length,
            (arm.data.bones[s_ + 'Foot'].head_local - arm.data.bones[s_ + 'Leg'].head_local).length)
       for s_ in ('Left', 'Right')}
LEG_BONES = ['Hips'] + [s_ + b for s_ in ('Left', 'Right') for b in ('UpLeg', 'Leg', 'Foot', 'ToeBase')]
N = 18
# Choreography (user review: "he only shows off his knives, he doesn't stab or slice"): two thrusts, alternating
# hands as the native keys do. Each hand chambers by its hip (elbow back, blade forward), thrusts fast at chest height
# with the arm extended and the chest turning into it, and recoils to a guard; then both daggers in guard, back to
# rest. Wrist targets (world, character faces -Y, +X his left), blade directions (toward a target point 0.9 m ahead at
# chest height for the thrusts), elbow poles (mirrored for the left), chest turn and lean.
KF = [0, 3, 5, 7, 9, 11, 15, 18]
TARGET = Vector((0.0, -0.95, 1.18))
CHAMBER, THRUST, GUARD = (1.0, 1.0, -0.6), (0.7, 0.2, -1.0), (1.0, 0.4, -0.8)
UPFWD, GUARDB = (0.0, -1.0, 0.25), (0.0, -0.9, 0.45)
R_THRUST, L_THRUST = (-0.08, -0.40, 1.20), (0.08, -0.40, 1.20)
aim_at = lambda w: tuple((TARGET - Vector(w)).normalized())
R_W = [None, (-0.27, 0.03, 1.05), R_THRUST, (-0.18, -0.22, 1.05), (-0.18, -0.22, 1.03), (-0.18, -0.24, 1.03),
       (-0.18, -0.26, 1.02), None]
R_B = [None, UPFWD, aim_at(R_THRUST), GUARDB, GUARDB, GUARDB, GUARDB, None]
R_P = [None, CHAMBER, THRUST, GUARD, GUARD, GUARD, GUARD, None]
L_W = [None, (0.18, -0.20, 1.00), (0.19, -0.18, 1.00), (0.27, 0.03, 1.05), L_THRUST, (0.18, -0.22, 1.05),
       (0.18, -0.26, 1.02), None]
L_B = [None, GUARDB, GUARDB, UPFWD, aim_at(L_THRUST), GUARDB, GUARDB, None]
L_P = [None, GUARD, GUARD, CHAMBER, THRUST, GUARD, GUARD, None]
CHEST = [0, 6, -14, 0, 14, 0, 0, 0]       # turn about Z (deg): + turns the right shoulder back
LEAN = [0, 2, 13, 5, 13, 5, 3, 0]
LOW = GUARD
# Body (user 2026-10-14: "attack anim should use the body/legs at least a bit, not be totally stationary"): a lunge.
# The right foot steps forward on the first thrust and stays there through the second, the hips drive forward and
# down into each thrust and settle back, and the wrist targets ride the hip travel, so each stab carries the body
# forward. Keys over KF: hips forward (m, -Y), hips down (m); the step and its lift on their own keys.
HFWD = [0, -0.02, 0.12, 0.07, 0.15, 0.07, 0.04, 0]
HDOWN = [0, 0.02, 0.06, 0.04, 0.07, 0.04, 0.02, 0]
STEP = [(0, 0.0), (3, 0.0), (5, 0.20), (15, 0.20), (18, 0.0)]
LIFT = [(0, 0.0), (3, 0.0), (4, 0.05), (5, 0.0), (15, 0.0), (16.5, 0.04), (18, 0.0)]


def body_keys(f):
    return (curve(list(zip(KF, HFWD)), f), curve(list(zip(KF, HDOWN)), f), curve(STEP, f), curve(LIFT, f))


def shift(f):
    fwd, down, _, _ = body_keys(f)
    return Vector((0.0, -fwd, -down))
json.dump({'note': 'attack intent per key (viewer half-frame = 2 x frame): wrist target and blade direction',
           'keys': [{'frame': f, 'R': None if R_W[i] is None else {'wrist': list(Vector(R_W[i]) + shift(f)), 'blade': list(R_B[i])},
                     'L': None if L_W[i] is None else {'wrist': list(Vector(L_W[i]) + shift(f)), 'blade': list(L_B[i])}}
                    for i, f in enumerate(KF)]},
          open(os.path.join(common.WORK, 'attack_intent.json'), 'w'), indent=1)


def interp(keys, f, default):
    """Catmull-Rom through the keys over KF (C1: the hands do not stop at every key); None = the rest value."""
    vals = [Vector(default if k is None else k) for k in keys]
    for i in range(len(KF) - 1):
        if f <= KF[i + 1]:
            t = (f - KF[i]) / (KF[i + 1] - KF[i])
            p0, p1, p2, p3 = vals[max(i - 1, 0)], vals[i], vals[i + 1], vals[min(i + 2, len(vals) - 1)]
            # non-uniform key spacing: tangents scaled to the segment length
            d1 = (p2 - p0) * ((KF[i + 1] - KF[i]) / max(KF[min(i + 1, len(KF) - 1)] - KF[max(i - 1, 0)], 1e-6))
            d2 = (p3 - p1) * ((KF[i + 1] - KF[i]) / max(KF[min(i + 2, len(KF) - 1)] - KF[i], 1e-6))
            if i == 0:
                d1 = Vector((0, 0, 0))
            if i + 1 == len(KF) - 1:
                d2 = Vector((0, 0, 0))
            h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
            return p1 * h00 + d1 * h10 + p2 * h01 + d2 * h11
    return vals[-1]


L1 = {}; L2 = {}
for side in ('Left', 'Right'):
    S = arm.data.bones[side + 'Arm'].head_local; E = arm.data.bones[side + 'ForeArm'].head_local
    W = arm.data.bones[side + 'Hand'].head_local
    L1[side] = (E - S).length; L2[side] = (W - E).length
blade_local = {}
for side, sd in (('Left', 'L'), ('Right', 'R')):
    Rh = (arm.matrix_world @ arm.data.bones[side + 'Hand'].matrix_local).to_3x3().normalized()
    blade_local[side] = Rh.inverted() @ Vector(SEAT[sd]['axis'])


def ik(side, W, pole):
    S = arm.matrix_world @ arm.pose.bones[side + 'Arm'].head
    l1, l2 = L1[side], L2[side]
    v = W - S; d = min(v.length, (l1 + l2) * 0.995); u = v.normalized()
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d); h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    p = pole - u * pole.dot(u); p.normalize()
    E = S + u * a + p * h
    aim(side + 'Arm', side + 'ForeArm', E - S)
    aim(side + 'ForeArm', side + 'Hand', (S + u * d) - E)


def blade_world(side):
    Rh = (arm.matrix_world @ arm.pose.bones[side + 'Hand'].matrix).to_3x3().normalized()
    return Rh @ blade_local[side]


def chest_rot():
    return (arm.matrix_world @ arm.pose.bones['Spine'].matrix).to_quaternion()


def fore_rot(side):
    return (arm.matrix_world @ arm.pose.bones[side + 'ForeArm'].matrix).to_quaternion()


def hand_rot(side):
    return (arm.matrix_world @ arm.pose.bones[side + 'Hand'].matrix).to_quaternion()


def roll_forearm(side, tw):
    fa = arm.pose.bones[side + 'ForeArm']; ax = ((arm.matrix_world @ arm.pose.bones[side + 'Hand'].head) - (arm.matrix_world @ fa.head)).normalized()   # elbow -> wrist (Meshy tails are guesses)
    turn(side + 'ForeArm', Matrix.Rotation(math.radians(tw), 3, ax))


def swing_only(side, q):
    """The world rotation q without its twist about the forearm axis (the forearm roll owns the twist)."""
    fa = arm.pose.bones[side + 'ForeArm']
    ax = ((arm.matrix_world @ arm.pose.bones[side + 'Hand'].head) - (arm.matrix_world @ fa.head)).normalized()   # elbow -> wrist (Meshy tails are guesses)
    p_ = Vector((q.x, q.y, q.z)).project(ax)
    tw = Quaternion((q.w, p_.x, p_.y, p_.z)); tw.normalize()
    return q @ tw.inverted()


def aim_hand(side, Q):
    """Rotate the hand toward world orientation Q (minimal rotation), capped at WRIST_CAP."""
    q = Q @ hand_rot(side).inverted()                  # world rotation (rotation_difference is in the hand's frame:
    if q.w < 0:                                        # applied as a world turn it missed the solve by up to 70 deg)
        q = -q
    q = swing_only(side, q)
    if q.angle > WRIST_CAP:
        q = Quaternion().slerp(q, WRIST_CAP / q.angle)
    turn(side + 'Hand', q.to_matrix())


WRIST_CAP = math.radians(40)
ROLL_MAX = 50
# key solve with continuity: per key, the forearm roll (-80..80) and a capped wrist swing that best aim the blade,
# penalising roll, roll change and the change of the wrist rotation (hand vs forearm) from the previous key
# (independent per-key rolls jumped +60 -> -40 -> +60 and the hands turned ~100 deg in one 48 fps frame,
# trace_clip.py); between keys roll and wrist rotation are interpolated, so the hand follows the arm continuously
TW = {'Left': {}, 'Right': {}}; QH = {'Left': {}, 'Right': {}}
live(rest)
for side in ('Left', 'Right'):
    TW[side][0] = TW[side][18] = 0
    QH[side][0] = QH[side][18] = fore_rot(side).inverted() @ hand_rot(side)      # wrist rotation (hand vs forearm)
for side, Wk, Bk, Pk in (('Right', R_W, R_B, R_P), ('Left', L_W, L_B, L_P)):
    sx = 1 if side == 'Left' else -1
    prevQ, prevT = QH[side][0], 0
    for i, f in enumerate(KF):
        if Wk[i] is None:
            continue
        base = world_turns(rest, [('Spine02', (0, 0, 1), CHEST[i]), ('Spine02', (1, 0, 0), LEAN[i])])
        base = body_motion(base, *body_keys(f)[:2], 0.0, *body_keys(f)[2:])
        pole = Vector((sx * Pk[i][0], Pk[i][1], Pk[i][2])).normalized()
        B = Vector(Bk[i]).normalized()
        best = (1e9, None)
        for tw in range(-ROLL_MAX, ROLL_MAX + 1, 5):
            live(base); ik(side, Vector(Wk[i]) + shift(f), pole); roll_forearm(side, tw)
            q = swing_only(side, blade_world(side).rotation_difference(B))
            if q.angle > WRIST_CAP:
                q = Quaternion().slerp(q, WRIST_CAP / q.angle)
            H = q @ hand_rot(side)
            Hc = fore_rot(side).inverted() @ H                 # the wrist rotation this solution needs
            err = math.degrees((q @ blade_world(side)).angle(B))
            cont = math.degrees(prevQ.rotation_difference(Hc).angle)
            cont = min(cont, 360 - cont)
            cost = err + 0.12 * abs(tw) + 0.25 * cont + 0.4 * abs(tw - prevT)
            if cost < best[0]:
                best = (cost, (tw, Hc, err, cont))
        tw, Hc, err, cont = best[1]
        TW[side][f], QH[side][f] = tw, Hc
        prevQ, prevT = Hc, tw
        print('ATTACK key', side, f, 'roll', tw, 'blade err %.0f' % err, 'wrist change from previous key %.0f' % cont)


def qcurve(keys, f):
    for (f0, q0), (f1, q1) in zip(keys, keys[1:]):
        if f <= f1:
            if q0.dot(q1) < 0:
                q1 = -q1
            return q0.slerp(q1, ease((f - f0) / (f1 - f0)))
    return keys[-1][1]


restW = {}
live(rest)
restW = {s: (arm.matrix_world @ arm.pose.bones[s + 'Hand'].head).copy() for s in ('Left', 'Right')}
restB = {s: blade_world(s).copy() for s in ('Left', 'Right')}
poses = []; fistw = []
report = []
for f in range(N + 1):
    chest = curve(list(zip(KF, CHEST)), f); lean = curve(list(zip(KF, LEAN)), f)
    base = world_turns(rest, [('Spine02', (0, 0, 1), chest), ('Spine02', (1, 0, 0), lean)])
    base = body_motion(base, *body_keys(f)[:2], 0.0, *body_keys(f)[2:])
    live(base)
    row = []
    for side, Wk, Bk, Pk in (('Right', R_W, R_B, R_P), ('Left', L_W, L_B, L_P)):
        sx = 1 if side == 'Left' else -1
        W = interp(Wk, f, tuple(restW[side])) + shift(f)
        P = interp([None if p is None else (sx * p[0], p[1], p[2]) for p in Pk], f, (sx * LOW[0], LOW[1], LOW[2]))
        ik(side, W, P.normalized())
        tw = curve([(k, TW[side][k]) for k in KF], f)
        roll_forearm(side, tw)
        aim_hand(side, fore_rot(side) @ qcurve([(k, QH[side][k]) for k in KF], f))
        B = interp(Bk, f, tuple(restB[side])).normalized()
        row.append((side, round(tw, 1), round(math.degrees(blade_world(side).angle(B)), 1)))
    w = ease(f / 2) if f <= 2 else (1.0 if f <= 15 else 1.0 - ease((f - 15) / 3))
    for sd in ('L', 'R'):
        fz = FIST[sd]
        for j, ang in enumerate(fz['fing']):
            arm.pose.bones[f'Fing{sd}{j + 1}'].rotation_quaternion = Quaternion(Vector((1, 0, 0)), math.radians(ang * w))
        arm.pose.bones[f'Thumb{sd}1'].rotation_quaternion = Quaternion().slerp(
            Euler(tuple(math.radians(x) for x in fz['thumb'][:3])).to_quaternion(), w)
        arm.pose.bones[f'Thumb{sd}2'].rotation_quaternion = Quaternion(Vector((1, 0, 0)), math.radians(fz['thumb'][3] * w))
    bpy.context.view_layer.update()
    p = capture()
    keep = dict(p)
    p = mix(rest, p, w)
    for n_ in [b for b in BONES if b.startswith(('Fing', 'Thumb'))]:
        p[n_] = keep[n_]
    # legs and hips follow the body keys, faded to Standing by the size of the body motion (no pop at the ends)
    fwd, down, step, lift = body_keys(f)
    wb = min(1.0, (abs(fwd) + abs(down) + step + lift) / 0.03)
    legs = mix(rest, {n_: keep[n_] if n_ in LEG_BONES else rest[n_] for n_ in BONES}, wb)
    for n_ in LEG_BONES:
        p[n_] = legs[n_]
    poses.append(p); fistw.append(w)
    report.append((f, row))
for r in report:
    print('ATTACK frame', r)
write('Attack', poses, dagger_scale=fistw)
set_action(A['Standing'])
bpy.ops.wm.save_mainfile()
