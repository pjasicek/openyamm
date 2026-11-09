"""Probe (m246 attack legs): per frame of the listed actions, world ankle (B_<s>_Foot head) and toe positions, pelvis
position and yaw, chest yaw. Prints a compact table. Args: -- <blend> action [...]"""
import bpy, sys, os, math
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
W = lambda b: rig.matrix_world @ rig.pose.bones[b].matrix
def yaw(b):
    M = W(b).to_3x3(); import mathutils
    f = M @ (rig.data.bones[b].matrix_local.to_3x3().inverted() @ mathutils.Vector((0, -1, 0)))
    return math.degrees(math.atan2(f.x, -f.y))
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    print('PROBE', an, 'frames', act.frame_range[:])
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        sc.frame_set(f)
        L, R, P = W('B_L_Foot').translation, W('B_R_Foot').translation, W('B_Pelvis').translation
        LT, RT = W('B_L_Toe0').translation, W('B_R_Toe0').translation
        print(f'PROBE {an} f{f:3d} L ({L.x:+.2f},{L.y:+.2f},{L.z:.2f}) toe z {LT.z:.2f} | R ({R.x:+.2f},{R.y:+.2f},{R.z:.2f}) toe z {RT.z:.2f} | pelvis ({P.x:+.2f},{P.y:+.2f},{P.z:.2f}) yaw {yaw("B_Pelvis"):+.0f} chest {yaw("B_Spine2"):+.0f}')
# pelvis path smoothness (m246 attack legs): world translation step per 1/30 s and its second difference
if os.environ.get('PELVIS_JERK'):
    import numpy as np
    for an in a[1:]:
        act = bpy.data.actions[an]; rig.animation_data.action = act
        if len(act.slots): rig.animation_data.action_slot = act.slots[0]
        P = []
        for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
            sc.frame_set(f); P.append(np.array(W('B_Pelvis').translation))
        P = np.array(P); v = np.linalg.norm(np.diff(P, axis=0), axis=1); acc = np.linalg.norm(np.diff(P, 2, axis=0), axis=1)
        print(f'PELVISJERK {an}: max step {v.max() * 100:.2f} cm/frame at {int(v.argmax())}, max second difference {acc.max() * 100:.2f} cm at {int(acc.argmax())}')
