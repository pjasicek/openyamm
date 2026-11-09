"""Build runtime clips from planted library retargets (work/locked.blend, keys at 30 fps) on the natf master:
1. resample to the master's 60 Hz (the accepted clips are keyed at 60 frames per second);
2. gaze: the head looks at the target (Standing's head direction), following only GAZE_FOLLOW of the chest's yaw and
   pitch change; the neck takes NECK_SHARE of the correction (Mixamo's sword-and-shield fighter stands side-on and
   turns his head to the target; planted square to the target, that turn made her look 30 deg left, then 50 deg right);
3. blend from Standing frame 0 over BLEND_IN s and back over BLEND_OUT s (local pose slerp, pelvis location lerp),
   so the engine's 0.12 s clip blend only covers small differences;
4. mounted wrist (Codex mounted_wrist.py rule): the right hand returns to its neutral relation to the forearm, ramped
   over WRIST_RAMP frames at both ends, because the blade is strapped along the forearm;
5. twist helpers baked with Codex's bake_twist.py.
Skirt_* and HemOpening keep their rest pose (the skirt is skinned to pelvis and thighs, see skirt_skin.py).
Also: the right elbow is kept in its anatomical hinge plane (the shared gate's elbow_plane rule: forearm direction
perpendicular to the upper arm's -Z hinge axis); SPINE damping slerps the spine bones toward Standing (the cast's chest
swings 110 deg in 0.1 s); the shield arm is anchored ANCHOR of the way to the pelvis instead of the chest (the long
shield swung into her hip when the chest twisted); the left twist helpers keep Standing's values (the shield arm holds
the Standing guard), only the right ones are baked.
Hip drive (optional 6th field, a free-leg retarget of the same source, retarget_mixamo.py :turn): the planted clip
holds pelvis and legs at Standing; the pelvis takes HIP_MOVE of the source's horizontal hip travel and turns HIP_YAW of
the chest's yaw change (the spine counter-turns, so the upper body and blade path keep their world motion), drops
HIP_DIP per metre of shift (plus whatever keeps both legs within REACH of their length), and both legs are solved
(two-bone, knee in its current bend plane) so the feet stay exactly where Standing plants them.
Usage: blender -b -P build_clips.py -- <in blend> <out blend> <source action>:<clip name>[:<speed>[:<gaze follow>[:<spine>[:<hip source action>]]]] [...]"""
import math
import os
import runpy
import sys

import bpy
from mathutils import Quaternion, Vector

a = sys.argv[sys.argv.index('--') + 1:]
src_blend, out_blend, items = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
GAZE_FOLLOW = float(os.environ.get('GAZE_FOLLOW', '0.3')); NECK_SHARE = 0.4
BLEND_IN = float(os.environ.get('BLEND_IN', '0.2')); BLEND_OUT = float(os.environ.get('BLEND_OUT', '0.25'))
WRIST_RAMP = 10
BONES = [b.name for b in rig.data.bones if not b.name.startswith(('Skirt_', 'HemOpening'))]
FWD = {n: rig.data.bones[n].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0)) for n in ('B_Head', 'B_Spine2')}


def use(act):
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def direction(n):
    return ((rig.pose.bones[n].matrix.to_3x3() @ FWD[n])).normalized()


def yaw_pitch(d):
    return math.atan2(d.x, -d.y), math.asin(max(-1.0, min(1.0, d.z)))


def from_yaw_pitch(y, p):
    return Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))


def rotate_world(n, R):
    """Rotate pose bone n by armature-space rotation R about its head."""
    pb = rig.pose.bones[n]; M = pb.matrix.copy(); t = M.translation.copy()
    M = R.to_matrix().to_4x4() @ M; M.translation = t; pb.matrix = M; bpy.context.view_layer.update()


def smooth(seq, passes=3):
    for _ in range(passes):
        seq = [seq[i] if i < 2 or i > len(seq) - 3 else
               (seq[i - 2] + 4 * seq[i - 1] + 6 * seq[i] + 4 * seq[i + 1] + seq[i + 2]) / 16 for i in range(len(seq))]
    return seq


def leg_ik(side, target):
    """Two-bone solve: thigh and calf swing so the foot head reaches target (armature space); the knee stays in the
    plane of its current bend; the foot takes the target's orientation."""
    th, ca, ft = (rig.pose.bones[f'B_{side}_{n}'] for n in ('Thigh', 'Calf', 'Foot'))
    H, K0, A0, A = th.head.copy(), ca.head.copy(), ft.head.copy(), target.translation.copy()
    L1, L2 = (K0 - H).length, (A0 - K0).length
    u = (A - H).normalized(); d = min((A - H).length, (L1 + L2) * 0.9995)
    x = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(0.0, L1 * L1 - x * x))
    pole = (K0 - H) - u * (K0 - H).dot(u); pole.normalize()
    rotate_world(th.name, (K0 - H).rotation_difference(H + u * x + pole * h - H))
    K1, A1 = ca.head.copy(), ft.head.copy()
    rotate_world(ca.name, (A1 - K1).rotation_difference(A - K1))
    M = target.copy(); M.translation = ft.head.copy(); ft.matrix = M; bpy.context.view_layer.update()


def key(f):
    for n in BONES:
        pb = rig.pose.bones[n]
        pb.keyframe_insert('rotation_quaternion', frame=f)
        if n == 'B_Pelvis':
            pb.keyframe_insert('location', frame=f)


for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'
# Standing frame 0: blend pose and the gaze reference (master actions are 60 Hz; set the scene rate first)
sc.render.fps = 60
use(bpy.data.actions['Standing']); sc.frame_set(0)
stand = {n: rig.pose.bones[n].matrix_basis.copy() for n in BONES}
head0 = yaw_pitch(direction('B_Head')); chest0 = yaw_pitch(direction('B_Spine2'))
pel0 = rig.pose.bones['B_Pelvis'].head.copy()
feet0 = {s: rig.pose.bones[f'B_{s}_Foot'].matrix.copy() for s in 'LR'}
leg0 = ((rig.pose.bones['B_L_Calf'].head - rig.pose.bones['B_L_Thigh'].head).length
        + (rig.pose.bones['B_L_Foot'].head - rig.pose.bones['B_L_Calf'].head).length)
# per-leg reach limit: never below Standing's own (0.98 of the leg length)
reach = {s: max(float(os.environ.get('REACH', '0.97')),
                (rig.pose.bones[f'B_{s}_Thigh'].head - feet0[s].translation).length / leg0 + 0.002) for s in 'LR'}
HIP_MOVE = float(os.environ.get('HIP_MOVE', '0.25')); HIP_YAW = float(os.environ.get('HIP_YAW', '0.4'))
HIP_DIP = float(os.environ.get('HIP_DIP', '0.35'))
ANCHOR = float(os.environ.get('ANCHOR', '0.5'))
stand_rel_pelvis = (rig.pose.bones['B_Pelvis'].matrix.to_quaternion().inverted()
                    @ rig.pose.bones['B_L_UpperArm'].matrix.to_quaternion())
HINGE = Vector((0, 0, -1))  # elbow hinge in the upper arm's bone frame (gate config elbow_hinge_axis)
LEFT_TWIST = ('B_L_ForearmTwist', 'B_L_UpperArmTwist')
stand_twist = {n: rig.pose.bones[n].matrix_basis.to_quaternion() for n in LEFT_TWIST}
report = []
for item in items:
    parts = item.split(':'); src_name, clip = parts[0], parts[1]; speed = float(parts[2]) if len(parts) > 2 else 1.0
    follow = float(parts[3]) if len(parts) > 3 else GAZE_FOLLOW
    spine = float(parts[4]) if len(parts) > 4 else 1.0
    hip_src = parts[5] if len(parts) > 5 else ''
    src = bpy.data.actions[src_name]
    # 1. resample: the source is keyed on 30 fps frames; output frame i at 60 Hz samples source frame i / 2 x speed
    s0, s1 = src.frame_range; n_out = int(round((s1 - s0) * 2 / speed))
    samples = []; hip_off = []; hip_yaw = []
    if hip_src:
        use(bpy.data.actions[hip_src])
        for i in range(n_out + 1):
            f = s0 + i * speed / 2; sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
            hip_off.append(rig.pose.bones['B_Pelvis'].head.copy())
        hip_off = smooth([Vector((p.x - hip_off[0].x, p.y - hip_off[0].y, 0.0)) * HIP_MOVE for p in hip_off])
    use(src)
    for i in range(n_out + 1):
        f = s0 + i * speed / 2; sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        samples.append({n: rig.pose.bones[n].matrix_basis.copy() for n in BONES})
        hip_yaw.append(yaw_pitch(direction('B_Spine2'))[0])
    hip_yaw = smooth([HIP_YAW * ((y - hip_yaw[0] + math.pi) % (2 * math.pi) - math.pi) for y in hip_yaw])
    max_shift = max_drop = max_turn = 0.0
    old = bpy.data.actions.get(clip)
    if old is not None:
        old.name = clip + '_codex'
    act = bpy.data.actions.new(clip); act.use_fake_user = True; use(act)
    fin, fout = BLEND_IN * 60, BLEND_OUT * 60
    max_gaze = 0.0
    for i, pose in enumerate(samples):
        for n in BONES:
            rig.pose.bones[n].matrix_basis = pose[n]
        bpy.context.view_layer.update()
        # hip drive: turn and shift the pelvis, the spine counter-turns (legs are solved after the blend)
        if hip_off:
            Rz = Quaternion((0, 0, 1), hip_yaw[i])
            rotate_world('B_Pelvis', Rz); rotate_world('B_Spine', Rz.inverted())
            pb = rig.pose.bones['B_Pelvis']; M = pb.matrix.copy(); M.translation += hip_off[i]; pb.matrix = M
            bpy.context.view_layer.update()
        # spine damping toward Standing (local), before anything is measured on the chest
        if spine < 1.0:
            for n in ('B_Spine', 'B_Spine1', 'B_Spine2'):
                pb = rig.pose.bones[n]; pb.rotation_quaternion = stand[n].to_quaternion().slerp(pb.matrix_basis.to_quaternion(), spine)
            bpy.context.view_layer.update()
        # shield arm: upper arm orientation ANCHOR of the way from chest-relative (the local lock) to pelvis-relative
        P = rig.pose.bones['B_Pelvis'].matrix.to_quaternion()
        U = rig.pose.bones['B_L_UpperArm'].matrix.to_quaternion()
        want_u = P @ stand_rel_pelvis
        rotate_world('B_L_UpperArm', Quaternion().slerp((want_u @ U.inverted()).normalized(), ANCHOR))
        # 2. gaze
        hy, hp = yaw_pitch(direction('B_Head')); cy, cp = yaw_pitch(direction('B_Spine2'))
        want = from_yaw_pitch(head0[0] + follow * (cy - chest0[0]), head0[1] + follow * (cp - chest0[1]))
        max_gaze = max(max_gaze, math.degrees(direction('B_Head').angle(want)))
        R = direction('B_Head').rotation_difference(want)
        rotate_world('B_Neck', Quaternion().slerp(R, NECK_SHARE))
        rotate_world('B_Head', direction('B_Head').rotation_difference(want))
        # 3. blend with Standing at both ends (smoothstep weights)
        w = min(1.0, i / fin if fin else 1.0, (n_out - i) / fout if fout else 1.0)
        w = w * w * (3 - 2 * w)
        if w < 1.0:
            for n in BONES:
                pb = rig.pose.bones[n]
                q = stand[n].to_quaternion().slerp(pb.matrix_basis.to_quaternion(), w)
                loc = stand[n].translation.lerp(pb.matrix_basis.translation, w)
                pb.rotation_quaternion = q
                if n == 'B_Pelvis':
                    pb.location = loc
            bpy.context.view_layer.update()
        # hip drive: drop with the shift (and enough to keep both legs within REACH), then plant the feet
        if hip_off:
            pb = rig.pose.bones['B_Pelvis']; shift = (pb.head - pel0).to_2d().length; drop = HIP_DIP * shift
            for s in 'LR':
                H = rig.pose.bones[f'B_{s}_Thigh'].head; A = feet0[s].translation
                horiz = (H - A).to_2d().length; top = A.z + math.sqrt(max(0.0, (reach[s] * leg0) ** 2 - horiz ** 2))
                drop = max(drop, H.z - top)
            M = pb.matrix.copy(); M.translation.z -= drop; pb.matrix = M; bpy.context.view_layer.update()
            for s in 'LR':
                leg_ik(s, feet0[s])
            max_shift = max(max_shift, shift); max_drop = max(max_drop, drop)
            max_turn = max(max_turn, abs(math.degrees(hip_yaw[i])))
        # right elbow in its hinge plane: rotate the forearm about its head by the out-of-plane angle
        up = rig.pose.bones['B_R_UpperArm']; fa = rig.pose.bones['B_R_Forearm']; hd = rig.pose.bones['B_R_Hand']
        h = (up.matrix.to_3x3() @ HINGE).normalized(); fdir = (hd.head - fa.head).normalized()
        inplane = (fdir - h * fdir.dot(h)).normalized()
        rotate_world('B_R_Forearm', fdir.rotation_difference(inplane))
        # 4. mounted wrist: neutral right hand away from the ends
        t = min(1.0, i / WRIST_RAMP, (n_out - i) / WRIST_RAMP); t = t * t * (3 - 2 * t)
        hb = rig.pose.bones['B_R_Hand']; hb.rotation_quaternion = hb.rotation_quaternion.slerp(Quaternion(), t)
        key(i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n_out
    report.append(f'{clip} <- {src_name}: {n_out + 1} frames at 60 Hz = {n_out / 60:.3f} s (speed {speed}), '
                  f'gaze correction max {max_gaze:.1f} deg'
                  + (f', hips shift max {max_shift * 100:.1f} cm, drop {max_drop * 100:.1f} cm, turn {max_turn:.1f} deg'
                     if hip_off else ''))
# temporal smoothing of the upper body (binomial 1-4-6-4-1, SMOOTH_PASSES times; ends held): the library snaps
# (cast thrust, slash peak) exceeded the shared gate's angular acceleration limit at 60 Hz
SMOOTH_PASSES = int(os.environ.get('SMOOTH_PASSES', '2'))
UPPER = [n for n in BONES if not any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe', 'Pelvis'))
         and n not in ('B_Neck', 'B_Head')]
for item in items:
    act = bpy.data.actions[item.split(':')[1]]; use(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    qs = {n: [] for n in UPPER}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for n in UPPER:
            q = rig.pose.bones[n].rotation_quaternion.copy()
            if qs[n] and qs[n][-1].dot(q) < 0:
                q.negate()
            qs[n].append(q)
    W = (1, 4, 6, 4, 1)
    for n in UPPER:
        seq = qs[n]
        for _ in range(SMOOTH_PASSES):
            out = []
            for i in range(len(seq)):
                if i < 2 or i > len(seq) - 3:
                    out.append(seq[i]); continue
                acc = Vector((0, 0, 0, 0))
                for k, w in zip(range(i - 2, i + 3), W):
                    acc += Vector(seq[k]) * w
                out.append(Quaternion(acc / 16).normalized())
            seq = out
        for i, q in enumerate(seq):
            pb = rig.pose.bones[n]; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f0 + i)
# 5. twist helpers (Codex bake_twist.py, run in this file's scene)
ns = runpy.run_path(os.path.join(HERE, '../mm6_natf_codex/scripts/bake_twist.py'))
for item in items:
    act = bpy.data.actions[item.split(':')[1]]
    ns['bake_twist'](act)
    use(act)
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        for n in LEFT_TWIST:
            pb = rig.pose.bones[n]; pb.rotation_quaternion = stand_twist[n]; pb.keyframe_insert('rotation_quaternion', frame=f)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
for r in report:
    print('CLIP', r)
