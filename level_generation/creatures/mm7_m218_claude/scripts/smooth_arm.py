"""Temporal smoothing of one arm's local rotations over a frame window (user review 2026-10-20: the spearman's right
elbow moved unevenly while the arm returned to the idle, attack frames 31-35). The clavicle, upper arm, forearm and hand
quaternions (sign-aligned) are Gaussian-filtered (sigma SIGMA frames) and blended in over BLEND frames at the window
edges, so the frames outside it are unchanged. Writes the action in place.
Args: -- <in blend> <out blend> <Action>:<side>:<first>-<last> ...   (env SIGMA=1.5 BLEND=3)"""
import bpy, sys, os
import numpy as np
from mathutils import Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
SIGMA, BLEND = float(os.environ.get('SIGMA', '1.5')), int(os.environ.get('BLEND', '3'))
k = np.arange(-4, 5); gk = np.exp(-0.5 * (k / SIGMA) ** 2); gk /= gk.sum()
for item in items:
    an, side, rng = item.split(':'); fa, fb = (int(x) for x in rng.split('-'))
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); frames = list(range(f0, f1 + 1))
    bones = [f'B_{side}_Clavicle', f'B_{side}_UpperArm', f'B_{side}_Forearm', f'B_{side}_Hand']
    Q = {n: [] for n in bones}
    for f in frames:
        sc.frame_set(f)
        for n in bones:
            q = rig.pose.bones[n].rotation_quaternion.copy()
            if Q[n] and q.dot(Q[n][-1]) < 0:
                q = -q
            Q[n].append(q)
    worst = 0.0
    for n in bones:
        arr = np.array([tuple(q) for q in Q[n]])
        pad = np.concatenate([np.repeat(arr[:1], 4, 0), arr, np.repeat(arr[-1:], 4, 0)])
        sm = np.stack([np.convolve(pad[:, c], gk, 'valid') for c in range(4)], 1)
        for i, f in enumerate(frames):
            if f < fa or f > fb:
                continue
            w = min(1.0, (f - fa + 1) / BLEND, (fb - f + 1) / BLEND)
            qs = Quaternion(tuple(sm[i])).normalized(); q = Q[n][i].slerp(qs, w)
            worst = max(worst, np.degrees(Q[n][i].rotation_difference(q).angle))
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=f)
    rig.animation_data.action = None
    print(f'SMOOTHARM {an} {side} frames {fa}-{fb}: sigma {SIGMA}, largest change {worst:.1f} deg')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
