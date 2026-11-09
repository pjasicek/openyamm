"""Per frame (and half frame) of an action: right/left elbow and wrist positions and the spear origin/axis.
Args: -- <blend> <action> <f0> <f1>"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; act = bpy.data.actions[a[1]]
rig.animation_data_create(); rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
W = lambda n: rig.matrix_world @ rig.pose.bones[n].matrix
f = float(a[2])
while f <= float(a[3]) + 1e-6:
    bpy.context.scene.frame_set(int(f), subframe=f % 1)
    r = lambda v: [round(x, 2) for x in v]
    print('ARM', f, 'R elbow', r(W('B_R_Forearm').translation), 'R wrist', r(W('B_R_Hand').translation),
          'L elbow', r(W('B_L_Forearm').translation), 'L wrist', r(W('B_L_Hand').translation),
          'spear', r(W('Spear').translation), 'axis', r(W('Spear').col[1].xyz))
    f += 0.5
