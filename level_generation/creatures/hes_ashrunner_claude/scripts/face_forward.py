"""Face the front in the set's cast and attack clips (the Unarmed casts and punches turn the head 40-60 degrees and the
chest up to 100 degrees to the side; the native casters face their target). Runs after plant.py, per frame of each
listed clip: each bone of the trunk chain, root first, is turned about the vertical through its joint so that its
world yaw (the heading of its rotated side axis, robust to bending forward) keeps only KEEP of what it has after its
parents' corrections; the head ends at KEEP_HEAD. The thighs keep their world rotations when the pelvis turns (the
planted legs stay). The arms ride on the chest, so a punch or cast then goes to the front.
Two passes: the per-frame corrections are measured first, smoothed over time (Gaussian, SMOOTH frames), then applied
(a per-frame correction followed the yaw estimate's noise while the head pitched forward: the Monk's head zig-zagged
up to 10 deg between frames in Attack; user review 2026-10-20).
Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
CHAIN = [('B_Pelvis', 0.3), ('B_Spine', 0.5), ('B_Spine1', 0.5), ('B_Spine2', 0.35), ('B_Neck', 0.2),
         ('B_Head', float(os.environ.get('KEEP_HEAD', '0.0')))]
SMOOTH = float(os.environ.get('FACE_SMOOTH', '2.0'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; AW = rig.matrix_world
THIGHS = [b.name for b in rig.data.bones if b.parent is not None and b.parent.name == 'B_Pelvis' and 'Thigh' in b.name]


def W(n):
    return AW @ rig.pose.bones[n].matrix


def set_world(n, M):
    rig.pose.bones[n].matrix = AW.inverted() @ M
    bpy.context.view_layer.update()


def yaw(n):
    R = W(n).to_3x3().normalized() @ rig.data.bones[n].matrix_local.to_3x3().inverted()
    s = R @ Vector((1, 0, 0))
    return math.atan2(s.y, s.x)


def turn(n, ang, legs=None):
    M = W(n); h = M.translation.copy()
    set_world(n, Matrix.Translation(h) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Translation(-h) @ M)
    if legs:
        for t, Mt in legs.items():
            out_ = Mt.to_3x3().to_4x4(); out_.translation = W(t).translation; set_world(t, out_)


def smooth(x, sig):
    if sig <= 0:
        return x
    r = int(math.ceil(3 * sig)); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
    xp = np.pad(np.unwrap(x), r, mode='edge'); return np.convolve(xp, k, mode='valid')


for name in acts:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    frames = list(range(f0, f1 + 1)); C = np.zeros((len(frames), len(CHAIN)))
    worst = [0.0, 0.0]
    for fi, f in enumerate(frames):                  # pass 1: measure (applied only to measure the children; not keyed)
        scene.frame_set(f)
        worst[0] = max(worst[0], abs(math.degrees(yaw('B_Head'))))
        legs = {t: W(t) for t in THIGHS}
        for ci, (n, keep) in enumerate(CHAIN):
            C[fi, ci] = -(1 - keep) * yaw(n)
            turn(n, C[fi, ci], legs if n == 'B_Pelvis' else None)
    for ci in range(len(CHAIN)):
        C[:, ci] = smooth(C[:, ci], SMOOTH)
    for fi, f in enumerate(frames):                  # pass 2: apply the smoothed corrections and key
        scene.frame_set(f)
        legs = {t: W(t) for t in THIGHS}
        for ci, (n, keep) in enumerate(CHAIN):
            turn(n, C[fi, ci], legs if n == 'B_Pelvis' else None)
        worst[1] = max(worst[1], abs(math.degrees(yaw('B_Head'))))
        for n in [c[0] for c in CHAIN] + THIGHS:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.keyframe_insert('rotation_quaternion', frame=f)
    print('FACE', name, 'frames', f1 - f0 + 1, 'head yaw max deg before', round(worst[0], 1), 'after', round(worst[1], 1))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
