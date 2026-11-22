"""Per frame of the listed actions: right/left hand world position (forward = -Y), speed (m/s) and the frames with
peak right-hand speed. Args: -- <blend> <action> [...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for name in a[1:]:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f1 = int(act.frame_range[1]); P = []
    for f in range(f1 + 1):
        sc.frame_set(f)
        P.append([np.array((rig.matrix_world @ rig.pose.bones[f'B_{s}_Hand'].matrix).translation) for s in 'RL'])
    P = np.array(P); v = np.linalg.norm(np.diff(P[:, 0], axis=0), axis=1) * 30
    rows = ' '.join(f'{f}:{-P[f,0,1]:+.2f}/{P[f,0,2]:.2f}/{(v[f-1] if f else 0):.1f}' for f in range(0, f1 + 1, 2))
    print('HANDS', name, 'frames', f1 + 1, '| R fwd/z/speed:', rows)
