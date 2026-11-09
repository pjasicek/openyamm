"""Aim the blaster straight ahead in the Attack (user review 2026-10-20: the set's pistol attack pointed the barrel up to
40 deg to his right at the shot; the native m475 attack fires toward the viewer). Runs after caster_timing.py, before
the twist bones and the cape simulation. Per frame, the barrel's heading (the Blaster bone's +Y, projected on the
floor) is measured; the right upper arm then turns about the vertical through the shoulder by minus that heading,
scaled by how raised the arm is (none while it hangs: upper arm direction z <= DZ0, full at z >= DZ1) and by KEEP
(1.0 = exactly ahead). The recoil's kick is capped: barrel pitch above PMAX deg is taken back at the shoulder (about
the horizontal axis across the barrel's heading; the regripped gun, regrip_blaster.py, sits 25 deg higher in the fist
and kicked to 53 deg). The corrections are smoothed over time (Gaussian, SMOOTH frames) before they are keyed, so the
raise and the recoil keep their motion; the forearm, hand and gun follow the upper arm.
Hold (user review 2026-10-20): the set's raise overshot (the muzzle rose 21 cm above the shot's height at 0.40 s and
sank back to it at the shot), so the arm read as up-down-fire. The right arm chain (clavicle, upper arm, forearm, hand)
now eases from its raise into the shot frame's pose (frame SHOT, the last aimed frame before the kick) between frames
HOLD_FROM and HOLD_FULL (smoothstep on the local rotations) and holds it until the shot; the kick and the return are
the set's.
Args: -- <in blend> <out blend> [Action ...] (default Attack)"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], (a[2:] or ['Attack'])
DZ0, DZ1 = float(os.environ.get('DZ0', '-0.7')), float(os.environ.get('DZ1', '-0.3'))
KEEP = float(os.environ.get('KEEP', '1.0')); SMOOTH = float(os.environ.get('SMOOTH', '1.5'))
PMAX = math.radians(float(os.environ.get('PMAX', '25')))
SHOT = int(os.environ.get('SHOT', '19')); HOLD_FROM = int(os.environ.get('HOLD_FROM', '4')); HOLD_FULL = int(os.environ.get('HOLD_FULL', '9'))
HOLD_BONES = ('B_R_Clavicle', 'B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand')
ARM = 'B_R_UpperArm'
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; AW = rig.matrix_world


def W(n):
    return AW @ rig.pose.bones[n].matrix


def barrel():
    return (W('Blaster').to_3x3() @ Vector((0, 1, 0))).normalized()


def heading():
    y = barrel()
    return math.atan2(y.x, -y.y)                     # 0 = straight ahead (-Y); positive = toward his left (+X)


def pitch():
    return math.asin(max(-1.0, min(1.0, barrel().z)))


def raised():
    pb = rig.pose.bones[ARM]; d = ((AW @ pb.tail) - (AW @ pb.head)).normalized()
    return min(1.0, max(0.0, (d.z - DZ0) / (DZ1 - DZ0)))


def turn(ang, axis='Z'):
    M = W(ARM); h = M.translation.copy()
    rig.pose.bones[ARM].matrix = AW.inverted() @ (Matrix.Translation(h) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-h) @ M)
    bpy.context.view_layer.update()


def lower(ang):
    y = barrel(); across = Vector((-y.y, y.x, 0.0))   # horizontal, across the heading: + rotation tips the barrel down
    if across.length > 1e-6 and abs(ang) > 1e-6:
        turn(ang, across.normalized())


def smooth(x, sig):
    r = int(math.ceil(3 * sig)); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
    return np.convolve(np.pad(x, r, mode='edge'), k, mode='valid')


for name in acts:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    frames = list(range(f0, f1 + 1)); C = np.zeros(len(frames)); K = np.zeros(len(frames)); before = []; kick = [0, 0]
    for i, f in enumerate(frames):
        scene.frame_set(f); w = raised(); hd = heading(); pt = pitch()
        C[i] = -KEEP * w * hd; K[i] = w * max(0.0, pt - PMAX); kick[0] = max(kick[0], math.degrees(pt))
        if w > 0.99:
            before.append(abs(math.degrees(hd)))
    C = smooth(C, SMOOTH); K = smooth(K, SMOOTH); after = []
    for i, f in enumerate(frames):
        scene.frame_set(f); turn(C[i]); lower(K[i]); kick[1] = max(kick[1], math.degrees(pitch()))
        pb = rig.pose.bones[ARM]; pb.rotation_mode = 'QUATERNION'; pb.keyframe_insert('rotation_quaternion', frame=f)
        if raised() > 0.99:
            after.append(abs(math.degrees(heading())))
    if name == 'Attack' and SHOT > 0:
        rec = {}
        for f in frames:
            scene.frame_set(f)
            rec[f] = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in HOLD_BONES}
        mz = []
        for f in range(HOLD_FROM, SHOT + 1):
            u = min(1.0, max(0.0, (f - HOLD_FROM) / (HOLD_FULL - HOLD_FROM))); w = u * u * (3 - 2 * u)
            scene.frame_set(f)
            for n in HOLD_BONES:
                pb = rig.pose.bones[n]; q0, q1 = rec[f][n], rec[SHOT][n]
                if q0.dot(q1) < 0:
                    q1 = -q1
                pb.rotation_quaternion = q0.slerp(q1, w); pb.keyframe_insert('rotation_quaternion', frame=f)
        for f in frames:
            scene.frame_set(f); mz.append((AW @ rig.pose.bones['Socket_Muzzle'].matrix).translation.z)
        shot_z = mz[frames.index(SHOT)]
        print('AIM hold', HOLD_FROM, '->', HOLD_FULL, 'until', SHOT, 'muzzle above the shot height before it, max cm',
              round(100 * (max(mz[:frames.index(SHOT)]) - shot_z), 1))
    print('AIM', name, 'raised frames', len(after), 'barrel heading max deg before', round(max(before, default=0), 1),
          'after', round(max(after, default=0), 1), 'largest arm turn', round(math.degrees(np.abs(C).max()), 1),
          'barrel pitch max deg before', round(kick[0], 1), 'after', round(kick[1], 1))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
