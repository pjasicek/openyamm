"""Per-frame right fingertip speed and velocity (world, m/s) in Attack and palm forward reach in Cast, to place the
impact/release events by eye on the numbers. Args: -- <blend>"""
import bpy, sys, os
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
def track(act, bn, tip):
    rig.animation_data.action = bpy.data.actions[act]
    if len(rig.animation_data.action.slots): rig.animation_data.action_slot = rig.animation_data.action.slots[0]
    out = []
    for f in range(int(rig.animation_data.action.frame_range[1]) + 1):
        sc.frame_set(f); pb = rig.pose.bones[bn]; out.append(np.array(rig.matrix_world @ (pb.tail if tip else pb.head)))
    return np.array(out)
p = track('Attack', 'B_R_Finger22', True); v = np.diff(p, axis=0) * 30
for i, (pp, vv) in enumerate(zip(p[1:], v)):
    print('ATK', i + 1, f'{(i + 1) / 30:.3f}s', 'pos', np.round(pp, 2), 'speed', round(float(np.linalg.norm(vv)), 2), 'vz', round(float(vv[2]), 2), 'vx', round(float(vv[0]), 2))
