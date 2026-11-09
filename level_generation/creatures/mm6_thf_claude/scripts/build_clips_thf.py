"""Native-timed clips for the thief (work/rig_v1.blend -> work/rig_v2.blend), after mm6_ttn1_claude/scripts/
build_clips_ttn.py. Native timings (mm6_thf/manifest.json): every sequence is 125 ms per frame; walk 6 frames
(0.75 s), attack/hit 0.75 s, death 0.75 s, fidget 0.75 s. The engine cuts attack and hit at the native length.
 - Standing (2 s loop): the bind pose upright, upper arms aimed down beside the hips (14 deg out, 4 deg forward),
   elbows bent 10 deg, a slow breath; hands relaxed (the native stand), daggers hidden.
 - Walking / Running: Meshy's rig clips (feet levelled, clavicles held by build_rig_thf.py); the arms keep 35 % / 45 %
   of their swing about the Standing arms, the run's knees and thighs 65 % (a jog: the sprint's heel kick went
   through the cloak) (the native walk barely swings the arms under the cloak).
 - Hit (0.75 s): Mixamo Medium Hit To Head retargeted onto Standing (retarget_hit.py, 2026-10-14).
 - Death (1.1 s, twice the source speed since 2026-10-14): Meshy Dying Backwards (DeathSrc) (knees buckle, falls on his back, as the native death),
   spine twist halved, upper-arm roll 60 %, wrists 60 % capped at 45 deg, eased from Standing; Dead holds its last pose.
 - Fidget (0.75 s): a look round over the right shoulder with a small shrug (the native fidget turns the head).
 Every frame of the authored clips is lifted on Hips so no vertex is below the floor. The dagger bones are keyed at
 scale 0.001 in every clip but Attack (attack_thf.py). Cloak chains are baked afterwards by cloak_sim.py."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
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
bind = {n: (Vector(), Quaternion()) for n in BONES}
live(bind)
HANG_OUT, HANG_FWD, ELBOW = 14.0, 4.0, 10.0
for side, sx in (('Left', 1), ('Right', -1)):
    o, f_ = math.radians(HANG_OUT), math.radians(HANG_FWD)
    aim(side + 'Arm', side + 'ForeArm', Vector((sx * math.sin(o), -math.sin(f_), -math.cos(o))))
    turn(side + 'ForeArm', Matrix.Rotation(math.radians(-ELBOW), 3, Vector((1, 0, 0))))
rest = capture()
stand = []
for f in range(49):
    w = math.sin(2 * math.pi * f / 48)
    stand.append(world_turns(rest, [('Spine01', (1, 0, 0), 1.0 * w), ('LeftArm', (0, 1, 0), 1.2 * w),
                                    ('RightArm', (0, 1, 0), -1.2 * w), ('Head', (1, 0, 0), -0.6 * w)]))
write('Standing', stand)
ARMS = [s + b for s in ('Left', 'Right') for b in ('Shoulder', 'Arm', 'ForeArm', 'Hand')]


def damp_arms(pose, keep):
    out = dict(pose)
    for n in ARMS:
        la, qa = rest[n]; lb, qb = pose[n]
        if qa.dot(qb) < 0:
            qb = -qb
        out[n] = (lb, qa.slerp(qb, keep))
    return out


RUN_LEG = 0.65
LEGS = [s + b for s in ('Left', 'Right') for b in ('UpLeg', 'Leg')]


def damp_legs(pose, keep):
    out = dict(pose)
    for n in LEGS:
        la, qa = bind[n]; lb, qb = pose[n]
        if qa.dot(qb) < 0:
            qb = -qb
        out[n] = (lb, qa.slerp(qb, keep))
    return out


for name, keep in (('Walking', 0.35), ('Running', 0.45)):   # 0.6: forearms 3 cm into the jerkin sides
    act = A[name]; f0, f1 = (int(round(x)) for x in act.frame_range)
    poses = [damp_arms(sample(act, f), keep) for f in range(f0, f1 + 1)]
    if name == 'Running':                 # bent pumping arms clipped the jerkin skirt by 2.5 cm: 6 deg further out
        poses = [world_turns(p, [('LeftArm', (0, 1, 0), -6), ('RightArm', (0, 1, 0), 6)]) for p in poses]
        # a jog, not a sprint: Meshy's run kicks the heel up behind through the cloak (the Rogue, speed 270 > 2.4 x
        # scale, runs all the time); knee and thigh swing kept at RUN_LEG of the source about the bind pose
        poses = [damp_legs(p, RUN_LEG) for p in poses]
    write(name, poses)
SPINE = ('Hips', 'Spine02', 'Spine01', 'Spine', 'neck', 'Head')


def untwisted(pose, bones, keep):
    out = dict(pose)
    for n in bones:
        loc, q = pose[n]
        p = Vector((q.x, q.y, q.z)).project(Vector((0, 1, 0)))
        tw = Quaternion((q.w, p.x, p.y, p.z)).normalized()
        swing = q @ tw.inverted()
        out[n] = (loc, (swing @ Quaternion().slerp(tw, keep)).normalized())
    return out


# Hit (user 2026-10-14: "hit - use better anim"): Mixamo Medium Hit To Head (0.93 s), retargeted relative to its first
# frame onto Standing (retarget_hit.py), resampled into the native 0.75 s and settled back into Standing over the last
# 5 frames. It replaced a held peak pose of Meshy Hit Reaction 1 (HitSrc), which read stiff.
import retarget_hit
HIT_FBX = os.path.join(common.PROJECT, '..', '..', '..', 'anim_library', 'mixamo', 'Medium Hit To Head.fbx')
write('Hit', retarget_hit.retarget(arm, HIT_FBX, frames=18, settle=5))
D1 = int(round(A['DeathSrc'].frame_range[1]))
def damp_wrists(pose, keep=0.6, cap=math.radians(45)):
    out = dict(pose)
    for n in ('LeftHand', 'RightHand'):
        loc, q = pose[n]; q = Quaternion().slerp(q, keep)
        if q.angle > cap:
            q = Quaternion().slerp(q, cap / q.angle)
        out[n] = (loc, q)
    return out


# spine twist halved; upper-arm roll 60 %; wrists 60 % capped at 45 deg (the source flings the hands: 68 deg)
# twice the source speed (user 2026-10-14: "death - speed up 2x"; it played at source speed, D1 frames at 24 fps)
DEATH_SPEED = 2.0
death = [damp_wrists(untwisted(untwisted(sample(A['DeathSrc'], min(f * DEATH_SPEED, D1)), ('Spine02', 'Spine01', 'Spine', 'Hips'),
                                         0.5), ('LeftArm', 'RightArm'), 0.6)) for f in range(int(math.ceil(D1 / DEATH_SPEED)) + 1)]
for i in range(4):
    death[i] = mix(rest, death[i], ease(i / 4))
write('Death', death)
write('Dead', [death[-1], death[-1]])
fid = []
for f in range(19):
    w = math.sin(math.pi * f / 18) ** 2
    fid.append(world_turns(rest, [('Spine', (0, 0, 1), -6 * w), ('neck', (0, 0, 1), -10 * w), ('Head', (0, 0, 1), -22 * w),
                                  ('Head', (1, 0, 0), -4 * w), ('LeftArm', (0, 1, 0), -4 * w),
                                  ('RightArm', (0, 1, 0), 4 * w)]))
write('Fidget', fid)
for name in ('Standing', 'Running', 'Hit', 'Death', 'Dead', 'Fidget'):   # Running: the damped knees reach 5 cm lower
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
scene['thf_rest'] = repr({n: (tuple(l), tuple(q)) for n, (l, q) in rest.items()})
set_action(A['Standing'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
