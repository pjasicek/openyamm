"""Game clips from the retargeted sources (work/anim_v1.blend) -> work/anim_v2.blend.

Upper body from the Mixamo sources (retarget_mixamo.py); the abdomen gets its own layer (the clips have no lower body):
  Standing  Breathing Idle, whole loop; abdomen sways on cycles that divide the loop.
  Attack    0.25 s ease from Standing into Standing Melee Attack Downward, source 0..1.40 s, then 0.25 s back to
            Standing. The right-hand blow (fastest down-forward claw, source 0.80 s) lands at 1.05 s, against the
            native 1.125 s action (actors.yml impact); the abdomen leans into the strike.
  Cast      the same lead-in into Standing 1H Magic Attack 01, source 0..1.35 s, release (fastest hand) at 1.02 s.
  Hit       Standing React Large From Front (1.0 s, within the native 1.125 s) as its change from its first frame on
            Standing (the source starts with hunched shoulders); the abdomen recoils.
  Death     authored from the native frames qdea0-qdee0 (no library clip sinks a body into rock): arms flung out
            (0.25 s), raised in a V (0.6 s), the rock collapses (scale 1 -> 0.66 tall, 1.06 wide, 0.5-1.5 s) while
            she sinks (Abdomen1 moved down until her skull base is 0.4 above the floor and forward until her head is
            0.15 in front of the rock's lower lobes, 0.7-1.6 s), arms lowered forward onto the ground, head bowed.
  Dead      the last Death pose held.
Every clip keys Root and Rock (rock at rest except in Death/Dead). Keys at 30 fps (the sources' rate)."""
import bpy, json, math
import numpy as np
from pathlib import Path
from mathutils import Quaternion, Vector, Matrix
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v1.blend'))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
FPS = 30
ABD = [f'Abdomen{i}' for i in range(1, 7)]
BONES = [pb.name for pb in rig.pose.bones]


def use(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def sample(name, t):
    """Local pose of every bone in source action `name` at time t (seconds)."""
    use(bpy.data.actions[name])
    f = t * FPS
    scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    return {pb.name: (pb.rotation_quaternion.copy() if pb.rotation_mode == 'QUATERNION'
                      else pb.matrix_basis.to_quaternion(), pb.location.copy(), pb.scale.copy())
            for pb in rig.pose.bones}


def ss(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def blend(a, b, w):
    out = {}
    for n in a:
        qa, la, sa = a[n]; qb, lb, sb = b[n]
        if qa.dot(qb) < 0:
            qb = -qb
        out[n] = (qa.slerp(qb, w), la.lerp(lb, w), sa.lerp(sb, w))
    return out


REST_W = {pb.name: (rig.matrix_world.to_3x3() @ rig.data.bones[pb.name].matrix_local.to_3x3()).to_quaternion()
          for pb in rig.pose.bones}


def world_delta(name, forward_deg, side_deg, W=None):
    """Local rotation that adds a world-space bend to bone `name`: forward_deg tips it toward -Y (her front, about
    world X), side_deg toward +X (about world Y). W: the bone's posed world rotation (rest frame when omitted)."""
    W = W or REST_W[name]
    D = Quaternion((0, 1, 0), math.radians(side_deg)) @ Quaternion((1, 0, 0), math.radians(forward_deg))
    return W.inverted() @ D @ W


def abdomen_layer(pose, angles):
    """World-space bends (forward, side degrees per abdomen bone) multiplied onto the pose (abdomen bones are not
    otherwise animated, so their rest frame stands in for the posed one)."""
    for n, (fwd, side) in zip(ABD, angles):
        q, l, s = pose[n]
        pose[n] = (q @ world_delta(n, fwd, side), l, s)
    return pose


def write(name, poses):
    if name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[name])
    act = bpy.data.actions.new(name); act.use_fake_user = True
    use(act)
    for i, pose in enumerate(poses):
        for pb in rig.pose.bones:
            q, l, s = pose[pb.name]
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = q; pb.location = l; pb.scale = s
            pb.keyframe_insert('rotation_quaternion', frame=i)
            pb.keyframe_insert('location', frame=i)
            pb.keyframe_insert('scale', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(poses) - 1
    use(None)
    print('CLIP', name, 'frames', len(poses), 'seconds', round((len(poses) - 1) / FPS, 3))
    return act


rest = {pb.name: (Quaternion(), Vector(), Vector((1, 1, 1))) for pb in rig.pose.bones}
src_len = {a.name: (a.frame_range[1] - a.frame_range[0]) / FPS for a in bpy.data.actions if a.name.endswith('_src')}
S0 = sample('Standing_src', 0.0)

# ---------------------------------------------------------------- Standing
T = src_len['Standing_src']
poses = []
for i in range(int(round(T * FPS)) + 1):
    t = i / FPS
    a = 2 * math.pi * t / (T / 3); b = 2 * math.pi * t / (T / 2)
    pose = sample('Standing_src', t)
    poses.append(abdomen_layer(pose, [(0.6 * math.sin(a + k * 0.5), 1.2 * math.sin(b + k * 0.6)) for k in range(6)]))
write('Standing', poses)


SPINE_KEEP = 0.65


def as_delta(poses):
    """Each pose as its change from the clip's first pose, applied on Standing (local: S0 * first^-1 * q): the clip
    starts exactly in Standing whatever the source body's own rest (the hit source starts with hunched shoulders)."""
    first = poses[0]
    out = []
    for pose in poses:
        p2 = {}
        for n, (q, l, sc) in pose.items():
            q0 = first[n][0]
            p2[n] = (S0[n][0] @ q0.inverted() @ q, S0[n][1] + (l - first[n][1]), sc)
        out.append(p2)
    return out


def one_shot(src, start, end, lead=0.25, tail=0.25, lean=None, neck_keep=1.0, delta=False, clav_keep=1.0,
             spine_keep=None):
    """lead s easing from Standing into src at `start`, src start..end, tail s easing back to Standing."""
    poses = []
    n_lead, n_src, n_tail = int(round(lead * FPS)), int(round((end - start) * FPS)), int(round(tail * FPS))
    first, last = sample(src, start), sample(src, end)
    for i in range(n_lead):
        poses.append(blend(S0, first, ss(i / n_lead)))
    body = [sample(src, start + i / FPS) for i in range(n_src + 1)]
    if delta:
        body = as_delta(body)
        last = body[-1]
    poses.extend(body)
    for i in range(1, n_tail + 1):
        poses.append(blend(last, S0, ss(i / n_tail)))
    # The queen's pelvis is planted on her abdomen, so the source's whole crouch and lunge lands in the spine (the
    # downward strike folded her head to her abdomen and tore the waist): keep SPINE_KEEP of the spine's motion.
    for pose in poses:
        for n in ('B_Spine', 'B_Spine1', 'B_Spine2'):
            q, l, sc = pose[n]; q0 = S0[n][0]
            if q.dot(q0) < 0:
                q = -q
            pose[n] = (q0.slerp(q, SPINE_KEEP if spine_keep is None else spine_keep), l, sc)
        for names, keep in ((('B_Neck', 'B_Head'), neck_keep), (('B_L_Clavicle', 'B_R_Clavicle'), clav_keep)):
            for n in names:
                q, l, sc = pose[n]; q0 = S0[n][0]
                if q.dot(q0) < 0:
                    q = -q
                pose[n] = (q0.slerp(q, keep), l, sc)
    if lean:
        for i, pose in enumerate(poses):
            abdomen_layer(pose, lean(i / FPS))
    return poses


def bump(t, a, peak, b):
    return ss((t - a) / (peak - a)) * (1 - ss((t - peak) / (b - peak)))


# The downward strike hunches hard: head below the shoulder line and the striking shoulder shrugged over the chest
# (user review 2026-10-13, frames 36-45): keep 50 % of the spine, 55 % of the neck/head and 60 % of the clavicle motion.
attack = one_shot('Attack_src', 0.0, 1.40, neck_keep=0.55, clav_keep=0.6, spine_keep=0.5,
                  lean=lambda t: [(5.0 * bump(t, 0.6, 1.05, 1.6) - 2.5 * bump(t, 0.2, 0.7, 1.0), 0.0)] * 6)
write('Attack', attack)
cast = one_shot('Cast_src', 0.0, 1.35, neck_keep=0.55, clav_keep=0.6, lean=lambda t: [(3.0 * bump(t, 0.6, 1.02, 1.5), 0.0)] * 6)
write('Cast', cast)
# the source whips the head back about 60 deg, which over-stretches her long neck: keep 60 % of the neck and head motion
hit = one_shot('Hit_src', 0.0, src_len['Hit_src'] - 0.1, lead=0.0, tail=0.1, neck_keep=0.6, delta=True,
               lean=lambda t: [(-5.0 * bump(t, 0.0, 0.2, 0.8), 2.0 * bump(t, 0.0, 0.3, 0.8))] * 6)
write('Hit', hit)


# ---------------------------------------------------------------- Death (authored)
def aim_pose(base, targets, head_pitch=0.0, spine_pitch=0.0):
    """Pose = base, with arm segments aimed at world directions targets {bone: (x, y, z)} (parents first) and an
    extra forward bend (degrees, world space; negative = back) on the spine and on the neck and head."""
    for pb in rig.pose.bones:
        q, l, s = base[pb.name]
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l; pb.scale = s
    bpy.context.view_layer.update()
    for n, ang in (('B_Spine1', spine_pitch), ('B_Spine2', spine_pitch), ('B_Neck', head_pitch), ('B_Head', head_pitch)):
        pb = rig.pose.bones[n]
        W = (rig.matrix_world @ pb.matrix).to_quaternion()
        pb.rotation_quaternion = pb.rotation_quaternion @ world_delta(n, ang, 0.0, W)
        bpy.context.view_layer.update()
    for n, d in targets.items():
        pb = rig.pose.bones[n]
        M = rig.matrix_world @ pb.matrix
        cur = M.to_3x3().col[1].normalized()
        R = cur.rotation_difference(Vector(d).normalized()).to_matrix().to_4x4()
        head = M.translation.copy()
        M2 = Matrix.Translation(head) @ R @ Matrix.Translation(-head) @ M
        pb.matrix = rig.matrix_world.inverted() @ M2
        bpy.context.view_layer.update()
    return {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}


def arms(dir_up, dir_fore):
    t = {}
    for s, sg in (('L', 1), ('R', -1)):
        t[f'B_{s}_UpperArm'] = (sg * dir_up[0], dir_up[1], dir_up[2])
        t[f'B_{s}_Forearm'] = (sg * dir_fore[0], dir_fore[1], dir_fore[2])
    return t


use(None)
K = [(0.0, S0),
     (0.25, aim_pose(S0, arms((0.97, -0.15, 0.15), (0.95, -0.2, 0.25)), head_pitch=-12, spine_pitch=-6)),
     (0.6, aim_pose(S0, arms((0.45, -0.1, 0.89), (0.3, -0.1, 0.95)), head_pitch=-22, spine_pitch=-8)),
     (1.0, aim_pose(S0, arms((0.5, -0.15, 0.85), (0.35, -0.2, 0.92)), head_pitch=-10, spine_pitch=-4)),
     (1.6, aim_pose(S0, arms((0.55, -0.65, -0.52), (0.45, -0.75, -0.48)), head_pitch=28, spine_pitch=18))]
DEATH = 1.6
abd_bone = rig.data.bones['Abdomen1']
# The last key's head height (aim_pose leaves that pose on the rig): sink so the skull base ends HEAD_END above the
# floor, as the native corpse keeps her head and claws at the foot of the collapsed rock.
# The rock's lower front lobes stand in front of the niche, so she must also come forward past them: her head ends
# HEAD_CLEAR in front of the rock face at that height (ray cast along +Y at the head's x).
HEAD_END = 0.4
HEAD_CLEAR = 0.15
DEATH_BEND = 4.0                          # forward bend per abdomen bone at the end (six bones: 24 deg in all)
final = abdomen_layer({n: (q.copy(), l.copy(), sc.copy()) for n, (q, l, sc) in K[-1][1].items()}, [(DEATH_BEND, 0.0)] * 6)
for pb in rig.pose.bones:
    q, l, sc = final[pb.name]; pb.rotation_quaternion = q; pb.location = l; pb.scale = sc
bpy.context.view_layer.update()
head = rig.matrix_world @ rig.pose.bones['B_Head'].head
rock_ob = bpy.data.objects['Rock']
ok, loc, nrm, idx = rock_ob.ray_cast(Vector((head.x, -20.0, HEAD_END)), Vector((0, 1, 0)))
front_y = loc.y if ok else head.y
SINK_WORLD = Vector((0.0, min(0.0, front_y - HEAD_CLEAR - head.y), -(head.z - HEAD_END)))
print('DEATH final head before sink', [round(x, 3) for x in head], 'rock front', round(front_y, 3),
      'sink', [round(x, 3) for x in SINK_WORLD])
sink_local = abd_bone.matrix_local.to_3x3().inverted() @ SINK_WORLD
death = []
for i in range(int(round(DEATH * FPS)) + 1):
    t = i / FPS
    k = max(j for j in range(len(K)) if K[j][0] <= t)
    if k == len(K) - 1:
        pose = {n: (q.copy(), l.copy(), s.copy()) for n, (q, l, s) in K[k][1].items()}
    else:
        (ta, pa), (tb, pb_) = K[k], K[k + 1]
        pose = blend(pa, pb_, ss((t - ta) / (tb - ta)))
    q, l, s = pose['Abdomen1']
    pose['Abdomen1'] = (q, sink_local * ss((t - 0.7) / 0.9), s)
    sq = ss((t - 0.5) / 1.0)
    q, l, s = pose['Rock']
    pose['Rock'] = (q, l, Vector((1 + 0.06 * sq, 1 - 0.34 * sq, 1 + 0.06 * sq)))   # bone Y = world up
    abdomen_layer(pose, [(DEATH_BEND * ss((t - 0.8) / 0.8), 0.0)] * 6)
    death.append(pose)
write('Death', death)
write('Dead', [death[-1], death[-1]])
for a in [a for a in bpy.data.actions if a.name.endswith('_src')]:
    a.use_fake_user = True
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'anim_v2.blend'))
