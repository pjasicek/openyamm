"""Even walk bob (user review 2026-10-20: in every walk the head went down, up, down again around each heel strike:
the retargeted Mixamo Walk / Dwarf Walk carry a pelvis hitch of 1-3 cm after the contact). The pelvis height of each
listed loop is low-passed over the cycle (Fourier, harmonics up to KMAX of the clip length: one walk cycle = two steps,
so the bob itself is harmonic 2) and the legs are re-solved by two-bone IK to the original ankle positions with the
original knee planes and foot turns, so the feet stay where they were. Writes the actions in place.
Args: -- <in blend> <out blend> <Action> ...   (env KMAX=4)"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
KMAX = int(os.environ.get('KMAX', '4'))
LEG = ['B_Pelvis'] + [f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf', 'Foot')]


def set_act(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and len(x.slots):
        rig.animation_data.action_slot = x.slots[0]


def leg_ik(side, ankle, knee_ref, foot_rot):
    th, ca, ft = f'B_{side}_Thigh', f'B_{side}_Calf', f'B_{side}_Foot'
    H = armik.W(rig, th).translation; K = armik.W(rig, ca).translation; A = armik.W(rig, ft).translation
    L1, L2 = (K - H).length, (A - K).length
    d = Vector(ankle) - H; dist = min(d.length, (L1 + L2) * 0.999); u = d.normalized()
    p = Vector(knee_ref) - H; v = p - u * p.dot(u)
    v = v.normalized() if v.length > 1e-6 else u.orthogonal().normalized()
    c = max(-1.0, min(1.0, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)))
    Kn = H + L1 * (u * c + v * math.sqrt(1 - c * c))
    q = (K - H).normalized().rotation_difference((Kn - H).normalized())
    armik.set_world(rig, th, armik.rot_world(armik.W(rig, th), q.to_matrix() @ armik.W(rig, th).to_3x3().normalized()))
    Mc = armik.W(rig, ca)
    q2 = (armik.W(rig, ft).translation - Mc.translation).normalized().rotation_difference((H + u * dist - Mc.translation).normalized())
    armik.set_world(rig, ca, armik.rot_world(Mc, q2.to_matrix() @ Mc.to_3x3().normalized()))
    armik.set_world(rig, ft, armik.rot_world(armik.W(rig, ft), foot_rot))
    return (armik.W(rig, ft).translation - Vector(ankle)).length


for an in acts:
    act = bpy.data.actions[an]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); frames = list(range(f0, f1 + 1))
    set_act(act); snaps, legs, z = [], [], []
    for f in frames:
        sc.frame_set(f)
        snaps.append({pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones})
        legs.append({s: (armik.W(rig, f'B_{s}_Foot').translation.copy(), armik.W(rig, f'B_{s}_Calf').translation.copy(),
                         armik.W(rig, f'B_{s}_Foot').to_3x3().normalized()) for s in 'LR'})
        z.append(armik.W(rig, 'B_Pelvis').translation.z)
    z = np.array(z); n = len(z) - 1                                 # the last frame repeats the first
    F = np.fft.rfft(z[:n]); F[KMAX + 1:] = 0; zs = np.fft.irfft(F, n); zs = np.append(zs, zs[0])
    set_act(None); keys, miss = [], 0.0
    for i, f in enumerate(frames):
        for pb in rig.pose.bones:
            pb.matrix_basis = snaps[i][pb.name]
        bpy.context.view_layer.update()
        M = armik.W(rig, 'B_Pelvis'); M.translation.z = float(zs[i]); armik.set_world(rig, 'B_Pelvis', M)
        for s in 'LR':
            ank, knee, rot = legs[i][s]; miss = max(miss, leg_ik(s, ank, knee, rot))
        keys.append({nm: (rig.pose.bones[nm].rotation_quaternion.copy(), rig.pose.bones[nm].location.copy()) for nm in LEG})
    set_act(act)
    prev = {}
    for i, f in enumerate(frames):
        for nm, (q, l) in keys[i].items():
            pb = rig.pose.bones[nm]; pb.rotation_mode = 'QUATERNION'
            if nm in prev and q.dot(prev[nm]) < 0:
                q = -q
            prev[nm] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
            if nm == 'B_Pelvis':
                pb.location = l; pb.keyframe_insert('location', frame=f)
    set_act(None)
    d = (zs - z) * 100
    print(f'BOBSMOOTH {an}: pelvis height changed {d.min():+.1f}..{d.max():+.1f} cm (harmonics <= {KMAX}), bob '
          f'{(z.max() - z.min()) * 100:.1f} -> {(zs.max() - zs.min()) * 100:.1f} cm, ankle miss max {miss * 1000:.1f} mm')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
