"""Mouse role clips (Blender module, used by build_export.py): MM9 MOUSE.abc clips for the body, head and tail
(clips_mm9.py: monotone cubic resampling through the MM9 keys, loop seams closed), plus our own leg layer, since MM9's
mouse has no legs.

MM9 has three clips: stand (2.5 s: the head sniffs, the rest still), run (0.22 s: body bob, head sway, tail wave) and
die (1.03 s: the mouse rolls onto its back). Roles:
  Standing    = stand (paws planted)
  Running     = run (7 frames), two bounding strides per clip like MM9's two body hops (paws down at each low point)
  Walking     = run at half rate (13 frames) with its body bob and roll at 40 %, a diagonal walk (FL+HR, FR+HL)
  Fidget      = stand plus a look-around (Bone08 turns left then right, a sniff on Bone06, a tail flick), 2.4 s
  Hit         = a flinch (body pulls back and up, nose up, tail flick), 0.5 s, paws planted
  Death       = die; the paws curl in as it rolls over (forward kinematics)
  Dead        = Death's last pose
Legs: one bone per paw (wrist/heel -> toes) placed per frame in armature space and keyed as plain local transforms;
stance paws stay fixed on the floor (z of the rest pose), swing paws lift in a sine arc riding up with the hop.
Every procedural channel is a smooth function of time (no per-frame noise); loops are periodic by construction.
"""
import math
import bpy
from mathutils import Quaternion, Vector, Matrix, Euler

import clips_mm9 as C

FPS = 30
RUN_FRAMES, WALK_FRAMES = 7, 13
STRIDE_RUN, STRIDE_WALK = 0.012, 0.009     # paw travel per cycle (model units): what the short legs can reach
LIFT = {'F': 0.0030, 'H': 0.0026}
LEGS = ('FL', 'FR', 'HL', 'HR')
# phase of each paw's touch-down (0..1) and stance share
# MM9's run bobs the body up 8 mm twice per 0.22 s cycle (two hops): the run has two bounding strides per clip, the
# paws planted around each low point (phase 0) and off the floor at the top of the hop; hind paws land first.
GAIT = {
    'Running': ({'HL': 0.70, 'HR': 0.72, 'FL': 0.80, 'FR': 0.82}, 0.5),
    'Walking': ({'FL': 0.0, 'HR': 0.0, 'FR': 0.5, 'HL': 0.5}, 0.62),
}
CYCLES = {'Running': 2, 'Walking': 1}
PITCH = {'F': 12.0, 'H': 0.0}   # toes flex down in the swing (the long hind foot stays level: its toes would dip)
ROLES = {
    'Standing': (['stand'], True),
    'Running': (['run'], 'rate:%.9f' % (0.22 / (RUN_FRAMES / FPS))),
    'Walking': (['run'], 'rate:%.9f' % (0.22 / (WALK_FRAMES / FPS))),
    'Fidget': (['stand'], False),
    'Hit': (['stand'], False),
    'Death': (['die'], False),
}


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def bump(t, a, b):
    """0 -> 1 -> 0 over [a, b] (raised cosine), 0 outside."""
    if t <= a or t >= b:
        return 0.0
    return 0.5 - 0.5 * math.cos(2 * math.pi * (t - a) / (b - a))


def fcurves(action):
    return C.fcurves(action)


def key_bone(arm, act, bone, frame, q=None, loc=None):
    pb = arm.pose.bones[bone]
    pb.rotation_mode = 'QUATERNION'
    if q is not None:
        pb.rotation_quaternion = q
        pb.keyframe_insert('rotation_quaternion', frame=frame)
    if loc is not None:
        pb.location = loc
        pb.keyframe_insert('location', frame=frame)


def channel_eval(act, bone, prop, frame, n):
    vals = []
    for i in range(n):
        fc = next((f for f in fcurves(act) if f.data_path == f'pose.bones["{bone}"].{prop}' and f.array_index == i),
                  None)
        vals.append(fc.evaluate(frame) if fc else (1.0 if (prop == 'rotation_quaternion' and i == 0) else 0.0))
    return vals


def add_offsets(arm, act, frames, fn):
    """fn(t) -> {bone: (euler_xyz_deg about armature axes, location offset in armature space)}: converted into the
    bone's rest frame and composed onto the MM9 keys (rotation after the MM9 rotation, location added), keyed at
    every frame (the MM9 keys are dense, one per frame, so each frame reads its own source value)."""
    for f in range(frames + 1):
        t = f / FPS
        for bone, (eul, dl_world) in fn(t).items():
            q0 = Quaternion(channel_eval(act, bone, 'rotation_quaternion', f, 4))
            l0 = Vector(channel_eval(act, bone, 'location', f, 3))
            R = arm.data.bones[bone].matrix_local.to_quaternion()
            dq = R.inverted() @ Euler([math.radians(a) for a in eul]).to_quaternion() @ R
            dl = R.inverted() @ dl_world
            arm.animation_data.action = act
            key_bone(arm, act, bone, f, q=q0 @ dq, loc=l0 + dl)


def scale_channels(arm, act, frames, bone, rot_share, loc_share):
    """Scale a bone's motion around its first-frame pose (rotation by slerp share, location by share): keyed at
    every frame, so it stays smooth and periodic when the source is."""
    q_rest = Quaternion()
    l_rest = Vector()
    for f in range(frames + 1):
        q0 = Quaternion(channel_eval(act, bone, 'rotation_quaternion', f, 4))
        l0 = Vector(channel_eval(act, bone, 'location', f, 3))
        key_bone(arm, act, bone, f, q=q_rest.slerp(q0, rot_share), loc=l_rest.lerp(l0, loc_share))


# ---------------------------------------------------------------- legs
def paw_path(leg, phase, gait, stride, bob=0.0):
    """Paw offset (dy, dz) from rest and paw pitch (deg) at cycle phase 0..1. Forward is -Y. A swinging paw lifts by
    its arc plus the body's rise (it rides up with the hop instead of hanging on a stretched stub)."""
    touch, stance = gait[0][leg], gait[1]
    s = (phase - touch) % 1.0
    if s < stance:                       # planted, moving back under the body
        u = s / stance
        return -stride / 2 + stride * u, 0.0, 0.0
    u = (s - stance) / (1 - stance)      # swing forward with a lift, toes flexed down
    e = smoothstep(u)
    lift = (LIFT[leg[0]] + max(bob, 0.0)) * math.sin(math.pi * u)
    return stride / 2 - stride * e, lift, PITCH[leg[0]] * math.sin(math.pi * u)


def bake_legs(arm, act, frames, path_fn):
    """path_fn(leg, t, bob) -> (dy, dz, pitch): the paw bone's armature-space placement from its rest (bob = the body's
    current rise above its rest, so a swinging paw rides up with the hop). Converted to the paw's local transform
    against the evaluated Bone05 at each frame; returns {frame: {bone: local matrix}}."""
    sc = bpy.context.scene
    arm.animation_data.action = act
    rest_body = arm.data.bones['Bone05'].head_local.z
    baked = {}
    for f in range(frames + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        bob = arm.pose.bones['Bone05'].head.z - rest_body
        mats = {}
        for leg in LEGS:
            name = f'Leg{leg}'
            pb = arm.pose.bones[name]
            dy, dz, pitch = path_fn(leg, f / FPS, bob)
            rest = pb.bone.matrix_local
            target = Matrix.Translation(rest.translation + Vector((0, dy, dz))) @ \
                Matrix.Rotation(math.radians(pitch), 4, 'X') @ rest.to_3x3().to_4x4()
            mats[name] = arm.convert_space(pose_bone=pb, matrix=target, from_space='POSE', to_space='LOCAL').copy()
        baked[f] = mats
    return baked


def key_baked(arm, act, baked):
    arm.animation_data.action = act
    for f, mats in baked.items():
        for b, m in mats.items():
            pb = arm.pose.bones[b]
            pb.rotation_mode = 'QUATERNION'
            loc, q, _ = m.decompose()
            pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=f)
            pb.location = loc
            pb.keyframe_insert('location', frame=f)


def linear_keys(act):
    for fc in fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'


# ---------------------------------------------------------------- roles
def fidget_offsets(t):
    """Look left then right (yaw about +Z), two sniffs (nose up: a negative rotation about +X lifts the -Y snout), a tail flick."""
    T = 2.4
    look = math.sin(2 * math.pi * t / T) * 22 * smoothstep(t / 0.4) * smoothstep((T - t) / 0.4)
    sniff = 6 * bump(t, 0.9, 1.5) + 4 * bump(t, 1.5, 1.9)
    flick = 18 * bump(t, 1.0, 1.8)
    return {'Bone08': ((0, 0, look), Vector()), 'Bone06': ((-sniff, 0, 0), Vector()),
            'Bone01': ((0, 0, flick), Vector())}


def hit_offsets(t):
    """A flinch: the body jerks back (+Y) and up with the nose raised, the head pulls in, the tail flicks; 0.5 s."""
    T = 0.5
    env = smoothstep(t / 0.08) * (1 - smoothstep((t - 0.12) / (T - 0.12)))
    return {'Bone05': ((-7 * env, 0, 0), Vector((0, 0.0035 * env, 0.0015 * env))),
            'Bone08': ((-8 * env, 0, 0), Vector()),
            'Bone01': ((0, 0, 25 * env), Vector())}


def build(arm):
    """Create all role actions on arm (MM9 actions present). Returns a report."""
    sc = bpy.context.scene
    fps_import = sc.render.fps / sc.render.fps_base
    originals = list(bpy.data.actions)
    report = C.build_role_clips(arm, fps_import, {k: v for k, v in ROLES.items() if k not in ('Fidget', 'Hit')})
    report.pop('_recs')
    # Fidget / Hit: the stand clip's opening, re-keyed with procedural offsets on top
    stand = bpy.data.actions['Standing']
    for role, T, fn in (('Fidget', 2.4, fidget_offsets), ('Hit', 0.5, hit_offsets)):
        act = stand.copy()
        act.name = role
        act.use_fake_user = True
        n = int(round(T * FPS))
        arm.animation_data.action = act
        # trim to n frames
        for fc in fcurves(act):
            for kp in reversed(list(fc.keyframe_points)):
                if kp.co.x > n + 1e-6:
                    fc.keyframe_points.remove(kp)
        add_offsets(arm, act, n, fn)
        report['clips'][role] = {'sources': ['stand'], 'procedural': fn.__name__, 'duration': n / FPS, 'frames': n}
    # Walking: the run body motion at 40 % (a walk does not bound)
    walk = bpy.data.actions['Walking']
    arm.animation_data.action = walk
    scale_channels(arm, walk, WALK_FRAMES, 'Bone05', 0.4, 0.4)
    report['clips']['Walking']['bone05_share'] = 0.4
    for a in originals:
        bpy.data.actions.remove(a)
    sc.render.fps = FPS
    sc.render.fps_base = 1
    # legs
    jobs = {}
    for role in ('Standing', 'Running', 'Walking', 'Fidget', 'Hit'):
        act = bpy.data.actions[role]
        frames = int(round(act.frame_range[1]))
        if role in GAIT:
            stride = STRIDE_RUN if role == 'Running' else STRIDE_WALK
            fn = (lambda g, s, fr, c: (lambda leg, t, bob: paw_path(leg, (c * t * FPS / fr) % 1.0, g, s, bob)))(
                GAIT[role], stride, frames, CYCLES[role])
        else:
            fn = lambda leg, t, bob: (0.0, 0.0, 0.0)
        jobs[role] = bake_legs(arm, act, frames, fn)
    for role, baked in jobs.items():
        key_baked(arm, bpy.data.actions[role], baked)
    # Death: paws curl towards the belly as the mouse rolls over (forward kinematics, eased in over the clip)
    death = bpy.data.actions['Death']
    frames = int(round(death.frame_range[1]))
    arm.animation_data.action = death
    for f in range(frames + 1):
        k = smoothstep(f / frames / 0.7)
        for leg in LEGS:
            # curl: the paw folds in towards the belly about its own lateral axis, drawn 2 mm into the body
            key_bone(arm, death, f'Leg{leg}', f, q=Euler((math.radians(40 * k), 0, 0)).to_quaternion(),
                     loc=Vector((0, 0, 0)))
    for act in bpy.data.actions:
        linear_keys(act)
    report['stride_per_clip'] = {'Running': STRIDE_RUN * CYCLES['Running'], 'Walking': STRIDE_WALK * CYCLES['Walking']}
    report['gait'] = {k: {'touch': v[0], 'stance': v[1]} for k, v in GAIT.items()}
    return report
