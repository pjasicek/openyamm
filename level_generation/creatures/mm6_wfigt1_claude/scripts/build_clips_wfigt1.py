"""Native-timed clips for the werewolf from the Mixamo Mutant clips retargeted by retarget_fbx.py onto the Meshy rig
(work/rig_v1.blend -> work/rig_v2.blend). Sources are keyed per source frame at 30 fps; output at 24 fps.
Native timings (mm6_wfigt1/manifest.json, 1/16 s ticks): walk 0.94 s, attack (wbite) 0.56 s, hit 0.75 s, death
0.69 s, fidget 1.0 s; the engine plays attack and hit on the AI clock (cut at the native length) and lets a longer
death finish first. Attack, Hit and Fidget start and end on Standing frame 0 (stand0).
 - Standing (4.0 s loop): Mutant Breathing Idle (spine, neck, head breathing), the last 8 frames cross-faded into
   frame 0; arms hung like the native stand (hang_arms: clavicles at bind, upper arms 17 deg out and 5 deg forward,
   elbows 28 deg, claws forward at upper-thigh height; user review: the Mutant arms read as bodybuilder flexing).
 - Walking / Running: Mutant Walking (1.43 s) / Mutant Run (0.87 s); exported with root travel, which is removed
   (hips XY drift, linear over the cycle; its length per cycle is the stride); the last frame repeats the first. Arms
   are the stand's hanging arms swung with the source's timing (+-22 deg walking, +-32 deg running with 60 deg
   elbows; the Mutant flung them 21-58 deg out).
 - Attack (0.5 s, 12 frames): an authored two-handed claw (user reviews: the roar lunge was weak, the swipe's arms
   flailed, the one-arm rake dislocated): hips and chest settle back while both arms rise with the claws by the head
   (frames 4-5), both claws rake forward and down as the hips drive 12 cm forward with planted feet (7), follow-through
   to waist height (9), back to the stand (12); jaw wide at the strike.
 - Hit (0.75 s, 18 frames): Zombie Reaction Hit source 4..44 (arms jerk up, head thrown back, recovers), eased in
   over 4 frames from the stance and out over 6; Jaw opens 14 deg.
 - Death (2.9 s, source speed since 2026-10-10): Mutant Dying source 0..86 (sinks, sits back, falls onto its back, as the native death),
   blended in from the stand over 7 frames;
   Dead holds the last pose; the lowest vertex of the corpse is put on the floor.
 - Fidget (1.0 s, 24 frames): authored from the stand like the native fidget: claws lift and flex at the hips,
   chest lifts, head turns toward the right shoulder with a snarl (the Mutant flex read as a forward reach).
Upright stance (in-game review: the Mutant crouch read squat and bulky next to the upright native stand): a
bone-space correction toward the bind pose on hips, spine (50 % of the crouch kept) and legs (35 %), applied to the
same clips; their feet are pinned to the floor every frame (the straighter legs would float).
Head level (review: the Mutant stance hung the head, snout 13-24 deg below level; the straightened spine then raised
it 30 deg): the head turned down 6 deg at the stance, the same bone-space correction, so the snout is about level
(the walk and run already hold it level; the death keeps its own head).
Every frame of every clip is lifted on Hips so its lowest vertex is not below z = 0 (Mixamo feet sink on our paws)."""
import bpy, sys, os, math, json
from mathutils import Vector, Quaternion, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
scene = bpy.context.scene
scene.render.fps = 24
arm = bpy.data.objects['Werewolf_Rig']; mesh = bpy.data.objects['Werewolf']
arm.animation_data_create()
BONES = [pb.name for pb in arm.pose.bones]
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
A = bpy.data.actions


def set_action(act):
    arm.animation_data.action = act
    if act is not None and getattr(act, 'slots', None):
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


def curve(keys, f):
    """Smoothstep interpolation through [(frame, value), ...]."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * ease((f - f0) / (f1 - f0))
    return keys[-1][1]


def with_jaw(pose, deg):
    """Jaw opened by deg about its local X (bone points forward along the snout; +X rotation drops the tip)."""
    out = dict(pose)
    loc, _q = pose['Jaw']
    out['Jaw'] = (loc, Quaternion(Vector((1, 0, 0)), math.radians(deg)))
    return out


def scaled_hips(pose, ref, k):
    out = dict(pose)
    l0 = ref['Hips'][0]; l, q = pose['Hips']
    out['Hips'] = (l0 + (l - l0) * k, q)
    return out


def write(name, poses):
    if name in A:
        A.remove(A[name])
    act = A.new(name); act.use_fake_user = True
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
    print('CLIP', name, 'frames 0 ..', len(poses) - 1, '(%.3f s)' % ((len(poses) - 1) / 24))
    return act


def retime(src, s0, s1, n):
    """n+1 output frames spanning source frames s0..s1."""
    return [sample(A[src], s0 + (s1 - s0) * f / n) for f in range(n + 1)]


stance = sample(A['MxIdle'], 0)
report = {}


def live(pose):
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location, pb.rotation_quaternion = pose[pb.name]
    bpy.context.view_layer.update()


def turn(bone, R):
    pb = arm.pose.bones[bone]
    M = arm.matrix_world @ pb.matrix; h = M.translation.copy()
    pb.matrix = arm.matrix_world.inverted() @ (Matrix.Translation(h) @ R.to_4x4() @ Matrix.Translation(-h) @ M)
    bpy.context.view_layer.update()


live(stance)
for bone, deg in (('Head', 6.0),):
    turn(bone, Matrix.Rotation(math.radians(deg), 3, Vector((1, 0, 0))))
LIFT = {b: stance[b][1].inverted() @ arm.pose.bones[b].rotation_quaternion.copy().normalized() for b in ('Head',)}
# stance straightened toward the bind pose (in-game review: the Mutant crouch, knees wide and claws near the ground,
# read far squatter and bulkier than the upright native stand): the share of the stance's rotation kept per bone
KEEP = {'Hips': 0.5, 'Spine02': 0.5, 'Spine01': 0.5, 'Spine': 0.5, 'LeftUpLeg': 0.35, 'RightUpLeg': 0.35,
        'LeftLeg': 0.35, 'RightLeg': 0.35, 'LeftFoot': 0.35, 'RightFoot': 0.35}
for b, k in KEEP.items():
    q = stance[b][1]
    LIFT[b] = q.inverted() @ Quaternion().slerp(q, k)


def lifted(poses):
    out = []
    for p in poses:
        p = dict(p)
        for b, c in LIFT.items():
            p[b] = (p[b][0], (p[b][1] @ c).normalized())
        out.append(p)
    return out


def capture():
    return {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy().normalized()) for pb in arm.pose.bones}


def aim(bone, tip, d):
    """Rotate `bone` about its head so the direction to the head of `tip` becomes d (world), smallest swing."""
    a = arm.matrix_world @ arm.pose.bones[bone].head; b = arm.matrix_world @ arm.pose.bones[tip].head
    turn(bone, (b - a).normalized().rotation_difference(d.normalized()).to_matrix())


# hanging arms like the native stand (user review: the Mutant idle held the shoulders 18 cm forward and the elbows
# bent 55-68 deg with the claws on the hips, "flexing for a bodybuilding competition"): clavicles at the bind pose,
# upper arms down and out beside the lats, elbows bent so the claws come forward at upper-thigh height
HANG_OUT, HANG_FWD, ELBOW, FORE_IN = 17.0, 5.0, 28.0, 5.0


def hang_arms(pose, sway=0.0, out=0.0, elbow=0.0, swing=None, base_elbow=ELBOW):
    """swing: {side: (upper-arm forward swing deg, extra elbow deg)} for locomotion."""
    live(pose)
    for side, sx in (('Left', 1), ('Right', -1)):
        sw, el = (swing or {}).get(side, (0.0, 0.0))
        for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand'):
            arm.pose.bones[side + b].rotation_quaternion = Quaternion()
        bpy.context.view_layer.update()
        o, f = math.radians(HANG_OUT + sway + out), math.radians(HANG_FWD + sw)
        aim(side + 'Arm', side + 'ForeArm', Vector((sx * math.sin(o), -math.sin(f) * math.cos(o),
                                                    -math.cos(f) * math.cos(o))))
        o2, f2 = math.radians(HANG_OUT - FORE_IN + sway + out), math.radians(HANG_FWD + sw + base_elbow + elbow + el)
        aim(side + 'ForeArm', side + 'Hand', Vector((sx * math.sin(o2), -math.sin(f2) * math.cos(o2),
                                                     -math.cos(f2) * math.cos(o2))))
    return capture()


# Standing: the breathing idle (spine, neck, head), loop closed by a cross-fade of the last 8 frames into frame 0;
# arms hung per frame with a slight breathing sway
n_idle = int(round((A['MxIdle'].frame_range[1] - A['MxIdle'].frame_range[0]) * 24 / 30))
stand = retime('MxIdle', 0, A['MxIdle'].frame_range[1], n_idle)
for i in range(8):
    k = n_idle - i
    stand[k] = mix(stand[k], stand[0], ease((8 - i) / 8))
stand[-1] = stand[0]
stand = [hang_arms(p, 1.2 * math.sin(2 * math.pi * f / n_idle)) for f, p in enumerate(lifted(stand))]
write('Standing', stand)
stand0 = stand[0]


def source_swing(pose):
    """Forward swing (deg, + forward) of each upper arm in a source pose, in the world side plane."""
    live(pose)
    out = {}
    for side in ('Left', 'Right'):
        a = arm.matrix_world @ arm.pose.bones[side + 'Arm'].head
        e = arm.matrix_world @ arm.pose.bones[side + 'ForeArm'].head
        d = (e - a).normalized()
        out[side] = math.degrees(math.atan2(-d.y, -d.z))
    return out


# locomotion arms (user review: the Mutant walk and run fling the arms wide, 21-58 deg out, and 70 deg back): the
# stand's hanging arms, swung fore and aft with the source's timing (its swing normalised to +-1 per side) by AMP,
# elbows bending further on the forward swing
LOCO_ARMS = {'Walking': (22.0, ELBOW, 14.0), 'Running': (32.0, 60.0, 18.0)}


def locomotion(src, name):
    act = A[src]
    s1 = act.frame_range[1]
    n = int(round(s1 * 24 / 30))
    poses = retime(src, 0, s1, n)
    p0, p1 = poses[0]['Hips'][0], poses[-1]['Hips'][0]
    # hips location is in the Hips bone's rest frame; drift measured in world through the armature
    hb = arm.data.bones['Hips']
    R = (arm.matrix_world.to_3x3() @ hb.matrix_local.to_3x3())
    d_world = R @ (p1 - p0)
    drift = Vector((d_world.x, d_world.y, 0.0))
    d_local = R.inverted() @ drift
    out = []
    for f, p in enumerate(poses):
        p = dict(p)
        l, q = p['Hips']
        p['Hips'] = (l - d_local * (f / n), q)
        out.append(p)
    amp, base_elbow, bend = LOCO_ARMS[name]
    sw = [source_swing(p) for p in out]
    rng = {sd: (min(x[sd] for x in sw), max(x[sd] for x in sw)) for sd in ('Left', 'Right')}
    for f, p in enumerate(out):
        swing = {}
        for sd, (lo, hi) in rng.items():
            t = (2 * (sw[f][sd] - lo) / max(hi - lo, 1e-3) - 1) * amp
            swing[sd] = (t, bend * max(t, 0.0) / amp)
        out[f] = hang_arms(p, swing=swing, base_elbow=base_elbow)
    out[-1] = out[0]
    report[name] = {'stride_m': round(drift.length, 3), 'seconds': round(n / 24, 3)}
    write(name, out)


locomotion('MxWalk', 'Walking')
locomotion('MxRun', 'Running')

# Attack (user review: use the swipe): Mutant Swiping SWIPE window (the left claw winds back and rakes across),
# hips and legs planted on the stand (the source leaps forward), half the hips rotation carried by the spine, the
# spine's twist about its axis at 40 % (the source spins the torso ~90 deg); eased from the
# stand over 2 frames and back over 3; the jaw opens with the rake
LOWER = ('LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase')
SWIPE_KEYS = [(0, 20), (5, 32), (9, 44), (12, 52)]


def untwisted(pose, bones, keep):
    """Each bone's local rotation with its twist about the bone axis (local Y) scaled by `keep` (swing kept)."""
    out = dict(pose)
    for n in bones:
        loc, q = pose[n]
        pr = Vector((q.x, q.y, q.z)).project(Vector((0, 1, 0)))
        tw = Quaternion((q.w, pr.x, pr.y, pr.z)).normalized()
        out[n] = (loc, ((q @ tw.inverted()) @ Quaternion().slerp(tw, keep)).normalized())
    return out


def planted(pose, base, hips_rot=0.5):
    """Hips and legs exactly on `base` (rotating the hips swung the planted legs apart); `hips_rot` of the source's
    hips rotation moves into Spine02, the lowest spine bone, so the upper body still turns with it."""
    out = dict(pose)
    for n in LOWER:
        out[n] = base[n]
    lb, qb = base['Hips']; _l, q = pose['Hips']
    if qb.dot(q) < 0:
        q = -q
    out['Hips'] = (lb, qb)
    l2, q2 = pose['Spine02']
    out['Spine02'] = (l2, (qb.inverted() @ qb.slerp(q, hips_rot) @ q2).normalized())
    return out


WRIST_CAP = math.radians(45)


def toward(pose, base, keep):
    """Per bone, the share `keep` of the source's local rotation, from `base` (with the hips planted, the slam bent the
    spine ~90 deg and hiked the clavicles, stretching the upper back into a sheet: review/gate_attack.png frame 8)."""
    out = dict(pose)
    for n, k in keep.items():
        lb, qb = base[n]; l, q = pose[n]
        if qb.dot(q) < 0:
            q = -q
        out[n] = (l, qb.slerp(q, k))
    return out


def aimed_arms(pose, base):
    """Arms pointing where the source points them, without the source's twist (titan stance_kept): upper arm,
    forearm and hand are aimed along the source segment directions starting from `base`'s arm (the hanging stand) with
    the smallest swing; clavicles stay the source's. The swipe's slam rolled the upper arm ~100 deg and stretched
    the shoulder blade into a sheet (review/gate_attack.png frame 8)."""
    live(pose)
    seg = {}
    for side in ('Left', 'Right'):
        P = {b: arm.matrix_world @ arm.pose.bones[side + b].head for b in ('Arm', 'ForeArm', 'Hand')}
        hand = (arm.matrix_world @ arm.pose.bones[side + 'Hand'].matrix).to_3x3().normalized() @ Vector((0, 1, 0))
        seg[side] = (P['ForeArm'] - P['Arm'], P['Hand'] - P['ForeArm'], hand)
    for side in ('Left', 'Right'):
        for b in ('Arm', 'ForeArm', 'Hand'):
            pb = arm.pose.bones[side + b]
            pb.location, pb.rotation_quaternion = base[side + b]
    bpy.context.view_layer.update()
    for side in ('Left', 'Right'):
        up, fore, hand = seg[side]
        aim(side + 'Arm', side + 'ForeArm', up)
        aim(side + 'ForeArm', side + 'Hand', fore)
        pb = arm.pose.bones[side + 'Hand']
        cur = (arm.matrix_world @ pb.matrix).to_3x3().normalized() @ Vector((0, 1, 0))
        q = cur.rotation_difference(hand)
        if q.angle > WRIST_CAP:
            q = Quaternion().slerp(q, WRIST_CAP / q.angle)
        turn(side + 'Hand', q.to_matrix())
    return capture()


# Attack (user review 4: frame 8 dislocated, the right arm sank into the shoulder in the follow-through; wanted a
# claw attack with both hands): a two-handed claw. Wind-up: hips and chest settle back, both arms raised out and up
# with the claws by the head, elbows near shoulder height (never straight up: the smallest swing from the hanging
# arm flips near vertical; upper arms 21 deg above horizontal, higher stretched the armpit and lats, user review 5);
# strike: both claws rake forward and down to converge in front of the chest while the hips drive ~12 cm forward
# (knees bend, feet planted by leg IK) and the chest leans in, jaw wide; follow-through to waist height; recover.
# Arm directions are world directions (he faces -Y, +X is his left), mirrored per side (sx); each upper arm stays on
# its own side of the body.
ATT_N = 12
V = lambda x, y, z: Vector((x, y, z)).normalized()
ANKLE = {sd: None for sd in ('Left', 'Right')}
live(stand0)
ANKLE = {sd: (arm.matrix_world @ arm.pose.bones[sd + 'Foot'].head).copy() for sd in ('Left', 'Right')}
FOOT = {sd: (arm.matrix_world @ arm.pose.bones[sd + 'Foot'].matrix).to_3x3().normalized() for sd in ('Left', 'Right')}
LEG = {sd: ((arm.pose.bones[sd + 'Leg'].head - arm.pose.bones[sd + 'UpLeg'].head).length,
            (arm.pose.bones[sd + 'Foot'].head - arm.pose.bones[sd + 'Leg'].head).length) for sd in ('Left', 'Right')}
# knee pole per side from the stand itself (user review 8: a straight-forward pole turned the stand's slightly
# outward knees inward, even at frame 0 of the attack)
POLE = {}
for sd in ('Left', 'Right'):
    H_ = arm.matrix_world @ arm.pose.bones[sd + 'UpLeg'].head
    K_ = arm.matrix_world @ arm.pose.bones[sd + 'Leg'].head
    u_ = (ANKLE[sd] - H_).normalized()
    POLE[sd] = ((K_ - H_) - u_ * (K_ - H_).dot(u_)).normalized()


def leg_ik(side, target, foot_world):
    """Two-bone leg IK: knee in the plane of the hip, the ankle target and a forward pole; the foot keeps its world
    orientation (flat on the floor)."""
    H = arm.matrix_world @ arm.pose.bones[side + 'UpLeg'].head
    l1, l2 = LEG[side]
    v = target - H; d = min(v.length, (l1 + l2) * 0.999); u = v.normalized()
    a_ = (l1 * l1 - l2 * l2 + d * d) / (2 * d); h = math.sqrt(max(l1 * l1 - a_ * a_, 0.0))
    pole = (POLE[side] - u * POLE[side].dot(u)).normalized()
    K = H + u * a_ + pole * h
    aim(side + 'UpLeg', side + 'Leg', K - H)
    aim(side + 'Leg', side + 'Foot', (H + u * d) - K)
    pb = arm.pose.bones[side + 'Foot']
    M = foot_world.to_4x4(); M.translation = arm.matrix_world @ pb.head
    pb.matrix = arm.matrix_world.inverted() @ M
    bpy.context.view_layer.update()


# key: frame, upper-arm and forearm directions for his left side (x mirrored for the right), hips forward (m, +
# forward), hips down (m), chest lean (deg, + forward), jaw (deg)
ATT_KEYS = [
    (0, None, 0.0, 0.0, 0.0, 0.0),
    (4, (V(0.84, -0.40, 0.36), V(0.05, -0.32, 0.95)), -0.05, 0.02, -9.0, 12.0),
    (5, (V(0.86, -0.36, 0.36), V(0.08, -0.26, 0.96)), -0.06, 0.03, -10.0, 16.0),
    (7, (V(0.35, -0.90, -0.20), V(-0.15, -0.85, -0.50)), 0.12, 0.06, 18.0, 28.0),
    (9, (V(0.32, -0.70, -0.64), V(-0.18, -0.45, -0.87)), 0.10, 0.06, 15.0, 22.0),
    (12, None, 0.0, 0.0, 0.0, 0.0)]


def hang_dirs():
    live(stand0)
    out = {}
    for side in ('Left', 'Right'):
        P = {b: arm.matrix_world @ arm.pose.bones[side + b].head for b in ('Arm', 'ForeArm', 'Hand')}
        out[side] = ((P['ForeArm'] - P['Arm']).normalized(), (P['Hand'] - P['ForeArm']).normalized())
    return out


HANG = hang_dirs()


def key_dirs(key, side, sx):
    if key[1] is None:
        return HANG[side]
    up, fore = key[1]
    return Vector((up.x * sx, up.y, up.z)), Vector((fore.x * sx, fore.y, fore.z))


att = []
for f in range(ATT_N + 1):
    k0, k1 = next((k0, k1) for k0, k1 in zip(ATT_KEYS, ATT_KEYS[1:]) if f <= k1[0])
    t = ease((f - k0[0]) / (k1[0] - k0[0]))
    fwd, down, lean, jaw = (k0[i] + (k1[i] - k0[i]) * t for i in (2, 3, 4, 5))
    live(stand0)
    pb = arm.pose.bones['Hips']
    pb.matrix = arm.matrix_world.inverted() @ (Matrix.Translation(Vector((0, -fwd, -down))) @ (arm.matrix_world @ pb.matrix))
    bpy.context.view_layer.update()
    turn('Spine02', Matrix.Rotation(math.radians(lean * 0.4), 3, Vector((1, 0, 0))))
    turn('Spine01', Matrix.Rotation(math.radians(lean * 0.6), 3, Vector((1, 0, 0))))
    turn('Head', Matrix.Rotation(math.radians(-lean * 0.5), 3, Vector((1, 0, 0))))
    if abs(fwd) + abs(down) > 1e-4:
        for side in ('Left', 'Right'):
            leg_ik(side, ANKLE[side], FOOT[side])
    for side, sx in (('Left', 1), ('Right', -1)):
        (u0, f0_), (u1, f1_) = key_dirs(k0, side, sx), key_dirs(k1, side, sx)
        for b in ('Arm', 'ForeArm', 'Hand'):
            q = stand0[side + b]
            arm.pose.bones[side + b].location, arm.pose.bones[side + b].rotation_quaternion = q
        bpy.context.view_layer.update()
        aim(side + 'Arm', side + 'ForeArm', u0.slerp(u1, t))
        aim(side + 'ForeArm', side + 'Hand', f0_.slerp(f1_, t))
    att.append(with_jaw(capture(), jaw))
write('Attack', att)
# continuity (the viewer interpolates between keys at 48 fps): largest per-frame rotation step of any arm/spine bone
steps = {}
for n in ('LeftArm', 'RightArm', 'LeftForeArm', 'RightForeArm', 'LeftHand', 'RightHand', 'Spine01', 'Hips'):
    steps[n] = round(max(math.degrees(att[i][n][1].rotation_difference(att[i + 1][n][1]).angle) for i in range(ATT_N)), 1)
print('ATTACK_STEPS', steps)

# Hit: zombie flinch; its own stance is more upright, so it is eased in from and out to ours
HIT_N = 18
hit = []
for f in range(HIT_N + 1):
    p = aimed_arms(lifted([scaled_hips(sample(A['MxHit'], 4 + 40 * f / HIT_N), stance, 0.4)])[0], stand0)
    w = ease(f / 4) if f <= 4 else (1.0 if f <= HIT_N - 6 else 1.0 - ease((f - (HIT_N - 6)) / 6))
    hit.append(with_jaw(mix(stand0, p, w), curve([(0, 0), (4, 14), (10, 10), (18, 0)], f)))
write('Hit', hit)

# Death: sinks, sits back, falls onto its back (native wdead); hips travel kept
DEATH_N = int(round(86 / 30 * 24))      # source speed (Mixamo 30 fps; 2026-10-10: it was 1.91x in 1.5 s)
death = retime('MxDeath', 0, 86, DEATH_N)
for i in range(7):                       # from the stand (user review: it started in the old Mutant crouch)
    death[i] = mix(stand0, death[i], ease(i / 7))
k = DEATH_N / 36                        # jaw keys authored on the 36-frame clip
death = [with_jaw(p, curve([(0, 0), (8 * k, 18), (24 * k, 22), (36 * k, 16)], f)) for f, p in enumerate(death)]
write('Death', death)
write('Dead', [death[-1], death[-1]])

# Fidget (1.0 s): authored from the stand like the native fidget (claws flex at the hips, head turns; user review:
# the Mutant flex without its twist read as a crouched forward reach): elbows bend 30 deg more and the arms ease
# 6 deg out (claws lift), the chest lifts 4 deg, the head turns 16 deg toward his right shoulder, jaw open 12 deg
FID_N = 24
fid = []
for f in range(FID_N + 1):
    w = math.sin(math.pi * f / FID_N) ** 2
    p = hang_arms(stand[f], 0.0, out=6 * w, elbow=30 * w)
    live(p)
    turn('Spine01', Matrix.Rotation(math.radians(-4 * w), 3, Vector((1, 0, 0))))
    turn('Head', Matrix.Rotation(math.radians(-16 * w), 3, Vector((0, 0, 1))))
    fid.append(with_jaw(capture(), 12 * w))
write('Fidget', fid)

# floor: each frame lifted on Hips so its lowest vertex is not below z = 0; the corpse lies on the floor
for name in ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Death', 'Dead', 'Fidget'):
    act = A[name]; set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    hips = arm.pose.bones['Hips']; mats = []; worst = 0.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        low = min((mesh.matrix_world @ v.co).z for v in m.vertices); ev.to_mesh_clear()
        pinned = name in ('Standing', 'Attack', 'Hit', 'Fidget') or (name in ('Death', 'Dead') and f == f1)
        lift = -low if (low < 0 or pinned) else 0.0
        worst = min(worst, low)
        mats.append((f, Matrix.Translation((0, 0, lift)) @ (arm.matrix_world @ hips.matrix)))
    for f, M in mats:
        scene.frame_set(f)
        hips.matrix = arm.matrix_world.inverted() @ M
        hips.keyframe_insert('location', frame=f)
    print('FLOOR', name, 'lowest vertex before', round(worst, 3))
print('LOCOMOTION', json.dumps(report))
json.dump(report, open(os.path.join(common.WORK, 'clips_report.json'), 'w'), indent=1)
for n in ('Walking_src', 'Running_src'):
    if n in A:
        A.remove(A[n])
set_action(A['Standing'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
