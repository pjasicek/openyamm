"""Low-pass listed bones' local rotations over time in listed clips (Monk Attack: the set's Unarmed Attack R2 snaps
the head 15 degrees between two frames and back, read as a zig-zag at the viewer's 48 fps; user review 2026-10-20).
Each bone's WORLD orientation track (sign-aligned quaternions) is Gaussian-smoothed over SIGMA frames and renormalised,
then applied per frame parent first (translation as evaluated): smoothing the local track instead let the head follow
the chest's own frame-to-frame swing, which its local rotation had been cancelling. The first and last frames keep their
values so loops and blends still meet. Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
BONES = os.environ.get('SMOOTH_BONES', 'B_Neck,B_Head').split(',')
SIGMA = float(os.environ.get('SMOOTH_SIGMA', '1.5'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']
r = int(math.ceil(3 * SIGMA)); K = np.exp(-0.5 * (np.arange(-r, r + 1) / SIGMA) ** 2); K /= K.sum()
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    AW = rig.matrix_world
    Q = {b: [] for b in BONES}
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        for b in BONES:
            Q[b].append(np.array((AW @ rig.pose.bones[b].matrix).to_quaternion()))
    QS = {}
    for b in BONES:
        q = np.array(Q[b])
        for i in range(1, len(q)):
            if q[i] @ q[i - 1] < 0:
                q[i] = -q[i]
        qs = np.stack([np.convolve(np.pad(q[:, c], r, mode='edge'), K, mode='valid') for c in range(4)], -1)
        qs[0], qs[-1] = q[0], q[-1]
        QS[b] = qs / np.linalg.norm(qs, axis=1, keepdims=True)
    for i, f in enumerate(range(f0, f1 + 1)):
        scene.frame_set(f)
        for b in BONES:                              # parents first (listed order)
            pb = rig.pose.bones[b]; pb.rotation_mode = 'QUATERNION'
            M = AW @ pb.matrix; R = Quaternion(QS[b][i]).to_matrix().to_4x4(); R.translation = M.translation
            pb.matrix = AW.inverted() @ R; bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print('SMOOTH', name, BONES, 'sigma', SIGMA)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
