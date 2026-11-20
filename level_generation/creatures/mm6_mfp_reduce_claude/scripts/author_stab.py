"""Cutpurse Attack: a right-hand dagger stab from Mixamo "Stabbing (1)" (retarget_mixamo.py :plant -> C_Stab1P: legs and
pelvis hold Standing frame 0, the upper body keeps the mocap with its chest yaw aligned to Standing).

Why this clip (review/attack/*.png, tip_probe.py): the humanoid set's dagger attacks R1-R3 are deep-guard leaps and
lunges, Mixamo "Stabbing" stabs with the left (lead) hand and "Stabbing (2)" swings the knife out to the side; "Stabbing
(1)" draws the right hand back and thrusts it forward at chest height (tip 0.77 m ahead, 1.34 m high).
Used: wind-up (source f4-22), thrust (f22-28), a short hold (f28-34), then back to Standing; the second slash and the
source's own recovery (f44-80) are dropped. Source time is remapped piecewise-linearly (TIMELINE, output seconds ->
source frame at 30 fps); every bone blends from and back to Standing frame 0 (smoothstep weight W_IN / W_OUT).
Right-hand fist and the Knife bone (visible) are the installed Attack's constant grip (Codex, round 1); the knife stays
hidden (scale 0.001) in every other clip, as installed. Braid, skirt and other unmapped bones hold Standing.
Twist bones are baked as in the Codex rig (forearm 0.6 x hand roll, upper arm -0.5 x its own roll).
Optional wrist aim (AIM_YAW_DEG): turn the right hand about world Z so the knife yaw at the thrust peak moves toward
straight ahead, weighted by a bell over the thrust and hold.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
from mathutils import Quaternion, Vector, Matrix
src_blend, out_blend = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
FPS = 30
SRC = os.environ.get('STAB_SRC', 'C_Stab1P')
TIMELINE = [(0.00, 4), (0.20, 10), (0.55, 22), (0.72, 28), (0.92, 34), (1.30, 38)]
W_IN, W_OUT = (0.0, 0.22), (0.92, 1.30)
AIM_YAW = math.radians(float(os.environ.get('AIM_YAW_DEG', '0')))       # extra hand yaw at the thrust (+ = toward her right)
AIM_BELL = (0.50, 0.70, 0.95, 1.15)                                      # ramp up, full, full, ramp down (s)
FA, UA = 0.6, 0.5
# wrist bend cap: the mocap bends the wrist ~64 deg in the thrust (88 with the aim), which folds the rigid bangles; the
# hand keeps its world orientation (knife direction) and the forearm swings about the elbow to take the excess
WRIST_MAX = math.radians(float(os.environ.get('WRIST_MAX_DEG', '30')))


def use(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def pose_at(act, f):
    use(act); sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    return {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def src_frame(t):
    for (t0, s0), (t1, s1) in zip(TIMELINE, TIMELINE[1:]):
        if t <= t1:
            return s0 + (s1 - s0) * (t - t0) / (t1 - t0)
    return TIMELINE[-1][1]


def weight(t):
    return smooth((t - W_IN[0]) / (W_IN[1] - W_IN[0])) * (1 - smooth((t - W_OUT[0]) / (W_OUT[1] - W_OUT[0])))


def bell(t):
    a, b, c, d = AIM_BELL
    return smooth((t - a) / (b - a)) * (1 - smooth((t - c) / (d - c)))


def twist_about(q, axis):
    v = Vector((q.x, q.y, q.z)); a = 2 * math.atan2(v.dot(axis), q.w)
    return (a + math.pi) % (2 * math.pi) - math.pi


old = bpy.data.actions['Attack']; old.name = 'Attack_codex'; old.use_fake_user = True
stand = pose_at(bpy.data.actions['Standing'], 0)
grip = pose_at(old, 0)
GRIP = [n for n in grip if n == 'Knife' or n.startswith('B_R_Finger')]
srca = bpy.data.actions[SRC]
dur = TIMELINE[-1][0]; n_out = int(round(dur * FPS))
frames = []
for i in range(n_out + 1):
    t = i / FPS; s = pose_at(srca, src_frame(t)); w = weight(t)
    p = {}
    for n, (q0, l0, k0) in stand.items():
        q1, l1, k1 = s[n]
        if q0.dot(q1) < 0:
            q1 = -q1
        p[n] = (q0.slerp(q1, w), l0.lerp(l1, w), k0.lerp(k1, w))
    for n in GRIP:
        p[n] = grip[n]
    frames.append((t, p))

act = bpy.data.actions.new('Attack'); act.use_fake_user = True
use(act)
prev = {}
for i, (t, p) in enumerate(frames):
    for n, (q, l, k) in p.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion, pb.location, pb.scale = q, l, k
    bpy.context.view_layer.update()
    if AIM_YAW and bell(t) > 0:
        pb = rig.pose.bones['B_R_Hand']; M = rig.matrix_world @ pb.matrix
        R = Matrix.Rotation(AIM_YAW * bell(t), 4, 'Z'); T = M.translation.copy()
        M = R @ M; M.translation = T
        pb.matrix = rig.matrix_world.inverted() @ M; bpy.context.view_layer.update()
    fbr, hbr = rig.data.bones['B_R_Forearm'], rig.data.bones['B_R_Hand']
    seg_r = (fbr.matrix_local.inverted() @ hbr.head_local).normalized()
    rest_rel_r = fbr.matrix_local.inverted() @ hbr.matrix_local
    pf, ph = rig.pose.bones['B_R_Forearm'], rig.pose.bones['B_R_Hand']
    H = rig.matrix_world @ ph.matrix; F = rig.matrix_world @ pf.matrix
    a_f = (F.to_3x3() @ seg_r).normalized()                                     # forearm axis (world)
    a_h = ((H @ rest_rel_r.inverted()).to_3x3() @ seg_r).normalized()           # forearm axis with no wrist bend
    bend = a_f.angle(a_h)
    if bend > WRIST_MAX:
        q = a_f.rotation_difference(a_h); ax, ang = q.to_axis_angle()
        R = Matrix.Rotation(bend - WRIST_MAX, 4, ax); T = F.translation.copy()
        F2 = R @ F; F2.translation = T
        pf.matrix = rig.matrix_world.inverted() @ F2; bpy.context.view_layer.update()
        H2 = H.copy(); H2.translation = (rig.matrix_world @ ph.matrix).translation
        ph.matrix = rig.matrix_world.inverted() @ H2; bpy.context.view_layer.update()
    for s_ in ('L', 'R'):
        fb, hb = rig.data.bones[f'B_{s_}_Forearm'], rig.data.bones[f'B_{s_}_Hand']
        seg = (fb.matrix_local.inverted() @ hb.head_local).normalized()
        rel = (rig.pose.bones[f'B_{s_}_Forearm'].matrix.inverted() @ rig.pose.bones[f'B_{s_}_Hand'].matrix).to_quaternion()
        rest_rel = (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion()
        tw = twist_about(rel @ rest_rel.inverted(), seg) * FA
        rig.pose.bones[f'B_{s_}_ForearmTwist'].rotation_quaternion = Quaternion(seg, tw)
        ub = rig.data.bones[f'B_{s_}_UpperArm']
        useg = (ub.matrix_local.inverted() @ rig.data.bones[f'B_{s_}_Forearm'].head_local).normalized()
        uq = rig.pose.bones[f'B_{s_}_UpperArm'].matrix_basis.to_quaternion()
        rig.pose.bones[f'B_{s_}_UpperArmTwist'].rotation_quaternion = Quaternion(useg, -UA * twist_about(uq, useg))
    for pb in rig.pose.bones:
        q = pb.rotation_quaternion
        if pb.name in prev and prev[pb.name].dot(q) < 0:     # sign-continuous keys
            pb.rotation_quaternion = -q
        prev[pb.name] = pb.rotation_quaternion.copy()
        pb.keyframe_insert('rotation_quaternion', frame=i)
        pb.keyframe_insert('location', frame=i); pb.keyframe_insert('scale', frame=i)
act.use_frame_range = True; act.frame_start, act.frame_end = 0, n_out
use(None)
for x in [a for a in bpy.data.actions if a.name.startswith('C_') and a.name != SRC]:
    x.use_fake_user = False
print(f'ATTACK {SRC}: {n_out + 1} frames = {dur:.2f} s at {FPS} fps, aim yaw {math.degrees(AIM_YAW):.0f} deg')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
