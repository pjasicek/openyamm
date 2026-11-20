"""Finger curl direction check: per finger, the distal joint and fingertip relative to the knuckle plane, signed along
the palm normal (palm_local: + = palm side). A fist must close toward the palm (positive values).
Args: -- <blend> <action> <frame> [side ...]"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); name, frame = a[1], int(a[2]); sides = a[3:] or ['R', 'L']
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions[name]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(frame)
for sd in sides:
    PL = armik.palm_local(rig, sd)
    Mh = (rig.matrix_world @ rig.pose.bones[f'B_{sd}_Hand'].matrix).to_3x3().normalized()
    n = np.array(Mh @ PL)
    out = []
    for i in range(1, 5):
        ch = [f'B_{sd}_Finger{i}', f'B_{sd}_Finger{i}1', f'B_{sd}_Finger{i}2']
        P = [np.array(rig.matrix_world @ rig.pose.bones[c].head) for c in ch]
        tip = np.array(rig.matrix_world @ rig.pose.bones[ch[2]].tail)
        out.append((i, round(float((P[2] - P[0]) @ n) * 100, 1), round(float((tip - P[0]) @ n) * 100, 1)))
    print('CURL', sd, name, frame, 'finger: (distal joint, tip) cm along the palm normal', out)
