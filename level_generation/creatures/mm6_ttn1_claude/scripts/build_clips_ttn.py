"""Native-timed clips for the titan from the Meshy library clips merged by build_rig_ttn.py (work/rig_v1.blend ->
work/rig_v2.blend). Native timings (mm6_ttn1/manifest.json): walk/attack/hit 0.75 s, death and fidget 0.625 s; the
engine plays attack and hit on the AI clock (cut at the native length) and lets a longer death finish first.
 - Standing (2 s loop, 48 frames): authored like the native stand (user review: Meshy's Idle 1 stooped, head forward,
   one forearm raised): the bind pose (upright spine, head level, legs straight) with the upper arms aimed down
   beside the hips (10 deg out, 6 deg forward) and the elbows bent 12 deg; a slow breath (chest, arms, head).
 - Attack (melee, 0.75 s): Meshy Right Upper Hook from Guard (HookSrc) 6..30, lunge halved, spine 60 %.
 - Ranged (0.75 s, 18 frames): Mixamo Standing 1H Magic Attack 01 (retarget_fbx.py) source 8..46: the right hand
   draws back, then thrusts forward, as the native lightning cast (user review: the Meshy cast stepped), eased in from
   and out to Standing frame 0 over 3 frames; hips and legs stay in the Standing pose (planted). The
   spine, neck and head take only 30 % of the source (STRAIGHTEN): the source body hunches.
 - Cast (2.0 s, 48 frames): Mixamo Two Hand Spell Casting source 8..86 (gather, two-handed push), planted, eased
   from and to Standing, then body_motion: weight back while channelling, a 22 cm step with the right foot and hips
   and chest driving forward on the release, back to the stance at the end (leg IK, flat feet); the engine needs a
   cast clip distinct from Attack for spellcasting monsters (Psychic Shock) and stretches it over the cast.
 - Hit (0.75 s): Standing -> Meshy Head Hold in Pain (HitSrc) frame 56 (bent forward, both hands on the helmet, as the
   native wince) at frame 6, held to frame 10, back to Standing at 18.
 - Death (2.2 s, source speed since 2026-10-10): Meshy Dying Backwards (DeathSrc, anim_death_v2), spine twist about the bone
   axes at 50 % (Shot and Fall Forward arched and wrung the torso), the first 4 frames eased from
   Standing; Dead holds its last pose. The lowest vertex of the corpse is put on the floor.
 - Fidget (0.625 s, 15 frames): Standing frame 0 with a procedural shrug: both upper arms lift away from the body,
   the chest rolls and the head turns toward the right shoulder, eased in and out (the native fidget flexes both
   hands at the hips; this rig has no finger chains). Turns are about world axes (local bone axes barely showed)."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
scene = bpy.context.scene
scene.render.fps = 24
arm = bpy.data.objects['Titan_Rig']; mesh = bpy.data.objects['Titan']
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


def write(name, poses):
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
    print('CLIP', name, 'frames 0 ..', len(poses) - 1, '(%.3f s)' % ((len(poses) - 1) / 24))
    return act


A = bpy.data.actions
bind = {n: (Vector(), Quaternion()) for n in BONES}
live(bind)
HANG_OUT, HANG_FWD, ELBOW = 10.0, 6.0, 12.0
for side, sx in (('Left', 1), ('Right', -1)):
    o, f_ = math.radians(HANG_OUT), math.radians(HANG_FWD)
    aim(side + 'Arm', side + 'Hand', Vector((sx * math.sin(o), -math.sin(f_), -math.cos(o))))
    turn(side + 'ForeArm', Matrix.Rotation(math.radians(-ELBOW), 3, Vector((1, 0, 0))))   # hand forward (faces -Y)
rest = capture()
ANKLE = {sd: (arm.matrix_world @ arm.pose.bones[sd + 'Foot'].head).copy() for sd in ('Left', 'Right')}
FOOT = {sd: (arm.matrix_world @ arm.pose.bones[sd + 'Foot'].matrix).to_3x3().normalized() for sd in ('Left', 'Right')}
LEG = {sd: ((arm.pose.bones[sd + 'Leg'].head - arm.pose.bones[sd + 'UpLeg'].head).length,
            (arm.pose.bones[sd + 'Foot'].head - arm.pose.bones[sd + 'Leg'].head).length) for sd in ('Left', 'Right')}
stand = []
for f in range(49):
    w = math.sin(2 * math.pi * f / 48)
    stand.append(world_turns(rest, [('Spine01', (1, 0, 0), 1.2 * w), ('LeftArm', (0, 1, 0), 1.5 * w),
                                    ('RightArm', (0, 1, 0), -1.5 * w), ('Head', (1, 0, 0), -0.8 * w)]))
write('Standing', stand)
SPINE = ('Hips', 'Spine', 'Spine01', 'Spine02', 'neck', 'Head')
STRAIGHTEN = 0.3


def untwisted(pose, bones, keep):
    """Each bone's local rotation with its twist about the bone axis (local Y) scaled by `keep` (swing kept)."""
    out = dict(pose)
    for n in bones:
        loc, q = pose[n]
        p = Vector((q.x, q.y, q.z)).project(Vector((0, 1, 0)))
        tw = Quaternion((q.w, p.x, p.y, p.z)).normalized()
        swing = q @ tw.inverted()
        out[n] = (loc, (swing @ Quaternion().slerp(tw, keep)).normalized())
    return out


LOWER = ('Hips', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot',
         'RightToeBase')


def planted(pose):
    """Hips and legs from the Standing rest pose: the source casts step and lunge, which slid the feet on a titan
    that does not move (user review: Ranged moved his legs)."""
    out = dict(pose)
    for n in LOWER:
        out[n] = rest[n]
    return out


WRIST_CAP = math.radians(45)


def stance_kept(src):
    """Planted legs and a 30 % spine (the source's crouched, turned stance is not the titan's); the arms point where
    the full source pose aims them (the Mixamo casters turn the chest ~90 deg into the thrust; with the chest
    straightened, local arm rotations spread the arms sideways into a T). Clavicles stay the titan's own; upper arm,
    forearm and hand are aimed along the source segment directions with the smallest swing, so no source twist is
    copied (copying world orientations rolled the upper arm 130 deg and collapsed the shoulder in the wind-up)."""
    live(src)
    seg = {}
    for side in ('Left', 'Right'):
        P = {b: arm.matrix_world @ arm.pose.bones[side + b].head for b in ('Arm', 'ForeArm', 'Hand')}
        hand = (arm.matrix_world @ arm.pose.bones[side + 'Hand'].matrix).to_3x3().normalized() @ Vector((0, 1, 0))
        seg[side] = (P['ForeArm'] - P['Arm'], P['Hand'] - P['ForeArm'], hand)
    live(planted(straightened(src)))
    for side in ('Left', 'Right'):
        for n in (side + 'Shoulder', side + 'Arm', side + 'ForeArm', side + 'Hand'):   # aim from the titan's rest
            pb = arm.pose.bones[n]; pb.location, pb.rotation_quaternion = rest[n]
        bpy.context.view_layer.update()
        up, fore, hand = seg[side]
        aim(side + 'Arm', side + 'ForeArm', up)
        aim(side + 'ForeArm', side + 'Hand', fore)
        pb = arm.pose.bones[side + 'Hand']
        cur = (arm.matrix_world @ pb.matrix).to_3x3().normalized() @ Vector((0, 1, 0))
        q = cur.rotation_difference(hand)
        if q.angle > WRIST_CAP:                         # wrist swing capped (the casters' flicked hands bent 62 deg)
            q = Quaternion().slerp(q, WRIST_CAP / q.angle)
        turn(side + 'Hand', q.to_matrix())
    return capture()


def straightened(pose):
    out = dict(pose)
    for n in SPINE:
        if n in out:
            la, qa = rest[n]; lb, qb = pose[n]
            if qa.dot(qb) < 0:
                qb = -qb
            out[n] = (lb, qa.slerp(qb, STRAIGHTEN))
    return out


# Ranged: Mixamo Standing 1H Magic Attack 01 (Mx1HSrc, retarget_fbx.py, 30 fps): source 8..46 (wind-up, right-hand
# thrust, hold) into 0.75 s; the wizard's crouched wide stance is not kept (planted legs, spine 30 %)
# Clip timing (2026-10-10, engine action events): Ranged, Attack and Cast play their source windows at source speed
# (N_* frames at 24 fps; they were squeezed 1.69x / 1.33x / 1.3x into 0.75 / 0.75 / 2.0 s, and the engine then
# squeezed the 2.0 s Cast into the 0.75 s cast action); the authored body-motion keys are scaled with them. The blow /
# release (IMPACT below) is the actors.yml `events` marker.
R0, R1 = 8, 46
N_R = int(round((R1 - R0) / 30 * 24))
R_LEAD = 0.2                                           # ready pause: the arm eases into the draw-back pose
cast = [stance_kept(sample(A['Mx1HSrc'], R0 + (R1 - R0) * f / N_R)) for f in range(N_R + 1)]
for i in range(3):
    cast[N_R - i] = mix(rest, cast[N_R - i], ease(i / 3))
# weight shift into the thrust (user: move the body into the release), no step
k = N_R / 18
for f in range(N_R + 1):
    cast[f] = body_motion(cast[f], curve([(0, 0), (5 * k, -0.03), (9 * k, 0.07), (15 * k, 0.06), (18 * k, 0)], f),
                          curve([(0, 0), (5 * k, 0.01), (9 * k, 0.03), (15 * k, 0.03), (18 * k, 0)], f),
                          curve([(0, 0), (5 * k, -3), (9 * k, 6), (15 * k, 5), (18 * k, 0)], f))
n_lead = int(round(R_LEAD * 24))
cast = [mix(rest, cast[0], ease(i / n_lead)) for i in range(n_lead)] + cast
write('Ranged', cast)

# Attack (melee, 0.75 s): Meshy Right Upper Hook from Guard (HookSrc) frames 6..30: the right fist winds back and
# hooks forward and up (user review: a fist on close range; the spell thrust became Ranged); the lunge on Hips is
# halved so the feet do not slide far, the spine keeps 60 % of the source (the hook turns the torso)
HOOK0, HOOK1 = 6, 30
N_A = HOOK1 - HOOK0                                    # Meshy clips are 24 fps
h0 = sample(A['HookSrc'], HOOK0)
punch = []
for f in range(N_A + 1):
    p = sample(A['HookSrc'], HOOK0 + (HOOK1 - HOOK0) * f / N_A)
    loc0 = h0['Hips'][0]
    p['Hips'] = (loc0 + (p['Hips'][0] - loc0) * 0.5, p['Hips'][1])
    punch.append(p)
saved = STRAIGHTEN
STRAIGHTEN = 0.6
punch = [straightened(p) for p in punch]
STRAIGHTEN = saved
A_LEAD = 0.35                                          # ready pause: the fists rise into the guard the hook starts from
for i in range(4):
    punch[N_A - i] = mix(rest, punch[N_A - i], ease(i / 4))
n_lead = int(round(A_LEAD * 24))
punch = [mix(rest, punch[0], ease(i / n_lead)) for i in range(n_lead)] + punch
write('Attack', punch)

# Cast (spellcasting monsters need a clip distinct from Attack; the engine stretches it over the cast): the whole
# Meshy cast, frames 2..62 retimed to 1.25 s, eased from and back to Standing frame 0
# Cast: Mixamo Two Hand Spell Casting (Mx2HSrc, 30 fps): source 8..86 (arms rise and gather, two-handed push forward,
# hold, release) into 2.0 s; planted legs, spine 30 %
C0, C1 = 18, 86                                        # from 18: the first arm rise-and-drop (8..18) is dropped
CAST_N = int(round((C1 - C0) / 30 * 24))
spell = [stance_kept(sample(A['Mx2HSrc'], C0 + (C1 - C0) * f / CAST_N)) for f in range(CAST_N + 1)]
BLEND = 6
for i in range(BLEND):
    out = 12 * math.sin(math.pi * i / BLEND)          # arms swing out while blending (a straight blend from the
    for k in (i, CAST_N - i):                          # hanging rest to the source's ready pose swept the left
        p = mix(rest, spell[k], ease(i / BLEND))       # forearm through the belly)
        spell[k] = world_turns(p, [('LeftArm', (0, 1, 0), -out), ('RightArm', (0, 1, 0), out)])
# channel and release (user review: "move his body a bit forward ... channel and release a spell"): while the arms
# gather (frames 6-18) the weight settles back; at the push (20-23) the right foot steps 22 cm forward, the hips drive
# forward and down and the chest leans in; held to frame 38, then he steps back (40-46)
def cf(f48):
    """Frame of the 48-frame authoring (source 8..86) in this clip's frames."""
    return (8 + (86 - 8) * f48 / 48 - C0) / (C1 - C0) * CAST_N


for f in range(CAST_N + 1):
    lift = 0.06 * (math.sin(math.pi * (f - cf(18)) / (cf(23) - cf(18))) if cf(18) <= f <= cf(23) else
                   (math.sin(math.pi * (f - cf(40)) / (cf(46) - cf(40))) if cf(40) <= f <= cf(46) else 0.0))
    spell[f] = body_motion(spell[f],
                           curve([(0, 0), (cf(8), -0.03), (cf(18), -0.04), (cf(23), 0.10), (cf(38), 0.09),
                                  (cf(46), 0)], f),
                           curve([(0, 0), (cf(8), 0.01), (cf(18), 0.02), (cf(23), 0.06), (cf(38), 0.05),
                                  (cf(46), 0)], f),
                           curve([(0, 0), (cf(8), -4), (cf(18), -5), (cf(23), 9), (cf(38), 8), (cf(46), 0)], f),
                           step=curve([(0, 0), (cf(18), 0), (cf(23), 0.22), (cf(40), 0.22), (cf(46), 0)], f),
                           lift=max(lift, 0.0))
write('Cast', spell)

pain = sample(A['HitSrc'], 56)
hit = []
for f in range(19):
    w = ease(f / 6) if f <= 6 else (1.0 if f <= 10 else 1.0 - ease((f - 10) / 8))
    hit.append(mix(rest, pain, w))
write('Hit', hit)

# Meshy Dying Backwards (189; the first death, Shot and Fall Forward, arched the chest back and bloated the cuirass,
# user review 104): staggers, sinks to the knees and falls back; spine twist about the bone axes kept at 50 %
D0 = 0
D1 = int(round(A['DeathSrc'].frame_range[1]))
# source speed (Meshy 24 fps; 2026-10-10: the engine finishes a longer death, it was 1.49x in 1.5 s)
death = [untwisted(sample(A['DeathSrc'], D0 + f), ('Spine02', 'Spine01', 'Spine', 'Hips'), 0.5)
         for f in range(D1 - D0 + 1)]
for i in range(4):
    death[i] = mix(rest, death[i], ease(i / 4))
write('Death', death)
write('Dead', [death[-1], death[-1]])


fid = []
for f in range(16):
    w = math.sin(math.pi * f / 15) ** 2
    # character faces -Y; +X is his left. Arms lift away from the body, elbows bend forward (fists up toward the
    # hips, like the native hands flexing at the waist), chest rolls, head turns toward his right shoulder
    # (signs: a turn about +Y moves a hanging left arm inward, about +X moves a hanging hand backward; the first
    # version had both the wrong way and pushed the arms into the hips, user review 105)
    fid.append(world_turns(rest, [('Spine02', (0, 1, 0), 3 * w), ('LeftArm', (0, 1, 0), -12 * w),
                                  ('RightArm', (0, 1, 0), 12 * w), ('LeftForeArm', (1, 0, 0), -22 * w),
                                  ('RightForeArm', (1, 0, 0), -22 * w), ('Head', (0, 0, 1), -18 * w)]))
write('Fidget', fid[:16])

# floor: Meshy's library clips sink the feet 2.5-4 cm (pose audit); each frame of every authored clip is lifted on
# Hips so its lowest vertex is not below z = 0 (the corpse lies on the floor)
for name in ('Standing', 'Attack', 'Ranged', 'Cast', 'Hit', 'Death', 'Dead', 'Fidget'):
    act = A[name]; set_action(act)
    f0, f1 = (int(round(x)) for x in act.frame_range)
    hips = arm.pose.bones['Hips']; mats = []; worst = 0.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        low = min((mesh.matrix_world @ v.co).z for v in m.vertices); ev.to_mesh_clear()
        lift = -low if (low < 0 or name in ('Death', 'Dead') and f == f1) else 0.0
        worst = min(worst, low)
        mats.append((f, Matrix.Translation((0, 0, lift)) @ (arm.matrix_world @ hips.matrix)))
    for f, M in mats:
        scene.frame_set(f)
        hips.matrix = arm.matrix_world.inverted() @ M
        hips.keyframe_insert('location', frame=f)
    print('FLOOR', name, 'lowest vertex before', round(worst, 3))
# blow / release: Attack = peak right-fist speed; Ranged = peak forward speed of the right hand; Cast = peak forward
# speed of the two hands together (the push). Characters face -Y.
for name in ('Attack', 'Ranged', 'Cast'):
    act = A[name]; set_action(act); hands = []
    for f in range(int(act.frame_range[1]) + 1):
        scene.frame_set(f)
        hands.append([arm.matrix_world @ arm.pose.bones[s + 'Hand'].head for s in ('Left', 'Right')])
    if name == 'Attack':                               # before the ease back to Standing
        v = [(hands[f + 1][1] - hands[f][1]).length for f in range(len(hands) - 6)]
    elif name == 'Ranged':
        v = [-(hands[f + 1][1] - hands[f][1]).y for f in range(len(hands) - 1)]
    else:
        v = [-(hands[f + 1][0] + hands[f + 1][1] - hands[f][0] - hands[f][1]).y for f in range(len(hands) - 1)]
    k = max(range(len(v)), key=v.__getitem__); impact = (k + 0.5) / 24
    print(f'IMPACT {name} {impact:.3f} s of {(len(hands) - 1) / 24:.3f} s (0.75 s action: wind-up stretch '
          f'{0.75 / impact:.2f}x)')
set_action(A['Standing'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
