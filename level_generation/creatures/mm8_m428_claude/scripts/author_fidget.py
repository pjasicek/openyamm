"""Native fidget (m428 F frames): she lifts the dagger in front of her chest, blade across her body toward her left,
looks down at it and runs her left fingers along the edge, then lowers it. 2.2 s at 30 fps (the engine finishes a
fidget whatever its length; native group 0.5 s). Built like the male's toss (mm8_m424_claude/scripts/
author_fidget.py): wrist paths are cubic Hermite curves through key points (world, Standing stance), the right arm
uses the global elbow-plane/hand-roll solve (armik.arm_dp) aiming the grip axis, the left arm a pole-vector IK with
a neutral wrist, head and neck pitch toward the blade. Starts and ends exactly on Standing frame 0.
In/out: work/rig_carry_twist.blend -> work/rig_fidget.blend."""
import bpy, sys, json, math, numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P / 'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/rig_carry_twist.blend'))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
G = json.loads((P / 'work/grip_pose.json').read_text()); AX = Vector(G['handle_axis_hand_local'])


def act(a):
    rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def restore(snap):
    act(None)
    for n, m in snap.items():
        rig.pose.bones[n].matrix_basis = m.copy()
    bpy.context.view_layer.update()


act(bpy.data.actions['Standing']); sc.frame_set(0)
ST = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
R0 = armik.W(rig, 'B_R_Hand').translation.copy(); L0 = armik.W(rig, 'B_L_Hand').translation.copy()
D0 = (armik.W(rig, 'B_R_Hand').to_3x3() @ AX).normalized()
POLE0 = (armik.W(rig, 'B_R_Forearm').translation - armik.W(rig, 'B_R_UpperArm').translation).normalized()
print('FIDGET rest right wrist', np.round(R0, 3), 'left wrist', np.round(L0, 3), 'dagger dir', np.round(D0, 3))


def curve(t, keys):
    times = np.array([k[0] for k in keys]); pts = np.array([tuple(k[1]) for k in keys])
    i = min(max(int(np.searchsorted(times, t) - 1), 0), len(keys) - 2)
    tang = [np.zeros(3) if j in (0, len(keys) - 1) else (pts[j + 1] - pts[j - 1]) / (times[j + 1] - times[j - 1])
            for j in range(len(keys))]
    h = times[i + 1] - times[i]; u = float(np.clip((t - times[i]) / h, 0, 1))
    return Vector((2 * u ** 3 - 3 * u * u + 1) * pts[i] + (u ** 3 - 2 * u * u + u) * h * tang[i]
                  + (-2 * u ** 3 + 3 * u * u) * pts[i + 1] + (u ** 3 - u * u) * h * tang[i + 1])


def smooth(x):
    x = float(np.clip(x, 0, 1)); return x * x * (3 - 2 * x)


# right wrist: up in front of the right breast, small lift while inspecting, back down
rkeys = [(0, R0), (0.45, (-0.10, -0.25, 1.15)), (0.75, (-0.08, -0.27, 1.19)), (1.45, (-0.07, -0.27, 1.20)),
         (1.80, (-0.13, -0.24, 1.12)), (2.2, R0)]
# left wrist: comes under the blade, slides 7 cm along it toward the tip (testing the edge), returns
# left keys 6.5 cm lower than first authored (3 cm, then 3.5 more for the re-tuned steeper blade): with the corrected fist (palm side, 2026-10-19 review) the blade sits
# 38 mm further in and passed 7.6 mm into the left fingers (fidget_touch.py)
lkeys = [(0, L0), (0.40, (0.18, -0.22, 1.03)), (0.75, (0.08, -0.29, 1.105)), (1.05, (0.06, -0.31, 1.145)),
         (1.35, (0.04, -0.32, 1.185)), (1.75, (0.20, -0.20, 1.01)), (2.2, L0)]
# up, forward and toward her left: about half pronation with the elbow down (the first version aimed the blade
# level across the body; the solver lifted the elbow and twisted the forearm ~155 deg, review/textured_frames)
BLADE = Vector((0.35, -0.40, 0.85)).normalized()   # re-tuned after the fist correction (fidget_sweep.py)
import os
if os.environ.get('FIDGET_BLADE'):
    BLADE = Vector(tuple(float(x) for x in os.environ['FIDGET_BLADE'].split(','))).normalized()
N = 66; frames = []
for f in range(N + 1):
    t = f / 30; restore(ST)
    look = smooth((t - 0.30) / 0.35) * (1 - smooth((t - 1.55) / 0.45))
    for n, ang, yaw in (('B_Neck', 0.14, 0.05), ('B_Head', 0.22, 0.10)):
        m = armik.W(rig, n); p = m.translation.copy()
        m = Matrix.Rotation(-ang * look, 4, 'X') @ Matrix.Rotation(yaw * look, 4, 'Z') @ m; m.translation = p
        armik.set_world(rig, n, m)
    armik.solve(rig, 'L', curve(t, lkeys), pole=Vector((0.40, 0.15, 1.05)))
    fa = armik.W(rig, 'B_L_Forearm').to_3x3().normalized()
    rel = rig.data.bones['B_L_Forearm'].matrix_local.to_3x3().inverted() @ rig.data.bones['B_L_Hand'].matrix_local.to_3x3()
    armik.set_world(rig, 'B_L_Hand', armik.rot_world(armik.W(rig, 'B_L_Hand'), fa @ rel))
    snap = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
    mix = smooth((t - 0.10) / 0.45) * (1 - smooth((t - 1.55) / 0.55))
    # elbow pole: the idle's own (akimbo, out-back) elbow at rest, blending to down/slightly out while the blade is up
    pole = POLE0.lerp(Vector((-0.35, 0.25, -1.0)).normalized(), mix).normalized()
    frames.append({'snap': snap, 'wrist': curve(t, rkeys), 'dir': D0.lerp(BLADE, mix).normalized(), 'pole': pole})
act(None)
choices = armik.arm_dp(rig, 'R', frames, AX, phis=range(-20, 21, 10), twist_neutral=30, k_twist=.6, k_phi=.5,
                       k_dphi=1, k_dpsi=.8, max_twist=90)   # elbow near the idle's (down) plane; wrist roll
# within 90 deg of neutral (after the 2026-10-19 fist correction the unconstrained solve rolled the hand -157 deg)
phi = np.array([c['phi'] for c in choices], float); psi = np.degrees(np.unwrap(np.radians([c['psi'] for c in choices])))
for a in (phi, psi):
    a[:] = np.convolve(np.pad(a, (2, 2), mode='edge'), np.array([1, 2, 3, 2, 1]) / 9, 'valid')
poses = []; stats = []
for f, fr in enumerate(frames):
    sw, tw = armik.apply_arm(rig, 'R', fr['snap'], fr['wrist'], AX, fr['dir'], phi[f], psi[f], pole=fr['pole'])
    stats.append((sw, tw))
    for n, q in G['finger_local'].items():
        rig.pose.bones[n].rotation_quaternion = Quaternion(q)
    poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
# exact Standing endpoints (the solve reproduces them only approximately)
act(bpy.data.actions['Standing']); sc.frame_set(0)
st = {b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones}
for f in range(N + 1):
    w = max(1 - smooth(f / 4), smooth((f - (N - 4)) / 4))
    poses[f] = {n: (q.slerp(st[n][0] if q.dot(st[n][0]) >= 0 else -st[n][0], w), l.lerp(st[n][1], w))
                for n, (q, l) in poses[f].items()}
old = bpy.data.actions.get('Fidget')
if old:
    bpy.data.actions.remove(old)
a = bpy.data.actions.new('Fidget'); a.use_fake_user = True; act(a); prev = {}
for f, p in enumerate(poses):
    for n, (q, l) in p.items():
        if n.startswith('Dress_'):
            continue
        b = rig.pose.bones[n]; b.rotation_mode = 'QUATERNION'
        if n in prev and q.dot(prev[n]) < 0:
            q = -q
        prev[n] = q.copy(); b.rotation_quaternion = q; b.location = l
        b.keyframe_insert('rotation_quaternion', frame=f)
        if n == 'B_Pelvis':
            b.keyframe_insert('location', frame=f)
a.use_frame_range = True; a.frame_start = 0; a.frame_end = N
act(None)
(P / 'work/fidget_plan.json').write_text(json.dumps({'duration_seconds': 2.2, 'gesture': 'inspect blade, left fingers along the edge',
    'swing_per_frame': [round(x[0], 1) for x in stats], 'twist_per_frame': [round(x[1], 1) for x in stats],
    'right_wrist_swing_max': max(x[0] for x in stats), 'twist_range': [min(x[1] for x in stats), max(x[1] for x in stats)]}, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/rig_fidget.blend'))
print('FIDGET', N + 1, 'frames; right wrist swing max', round(max(x[0] for x in stats), 1))
