"""Motion smoothness at the viewer's 48 fps: per action and bone (world rotation), the angle step per 1/48 s and its
change between consecutive steps (a jerk shows as a large second difference). Prints the worst step and the worst
second difference with their times. Args: -- <blend> <action> [...]"""
import bpy, sys, os, math
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); rig = bpy.data.objects['Rig']; sc = bpy.context.scene
BONES = os.environ.get('BONES', '').split(',') if os.environ.get('BONES') else ['B_Head', 'B_Neck', 'B_Spine2', 'B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand', 'B_L_UpperArm', 'B_L_Forearm', 'B_L_Foot', 'B_R_Foot']
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; ts = np.arange(f0, f1 + 1e-6, 30 / 48)
    Q = {b: [] for b in BONES}
    for f in ts:
        sc.frame_set(int(f), subframe=float(f - int(f)))
        for b in BONES: Q[b].append((rig.matrix_world @ rig.pose.bones[b].matrix).to_quaternion())
    out = []
    for b in BONES:
        st = np.array([math.degrees(q0.rotation_difference(q1).angle) for q0, q1 in zip(Q[b][:-1], Q[b][1:])])
        st = np.minimum(st, 360 - st); d2 = np.abs(np.diff(st))
        i, j = int(np.argmax(st)), int(np.argmax(d2)) if len(d2) else 0
        out.append(f'{b[2:]} step {st[i]:.1f}@{ts[i] / 30:.2f}s d2 {d2[j]:.1f}@{ts[j] / 30:.2f}s')
    print('JERK', an, '|', ' | '.join(out))
