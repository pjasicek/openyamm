"""hgd: body joints in the rifle frame (work/rifle_frame.json) per clip: where a stock and the barrel may go.
Args: -- <blend> <clip> [...]"""
import bpy, sys, os, json
import numpy as np
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Hr = Matrix(json.load(open(os.path.join(HERE, 'work', 'rifle_frame.json')))['rifle_in_hand'])
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for c in a[1:]:
    act = bpy.data.actions[c]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    pts = {}
    for f in (f0, (f0 + f1) // 2, f1):
        sc.frame_set(f)
        F = (rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix @ Hr).inverted()
        for n in ('B_R_UpperArm', 'B_R_Forearm', 'B_Spine2', 'B_Pelvis', 'B_Head', 'B_L_Forearm'):
            pts.setdefault(n, []).append([round(x, 2) for x in F @ (rig.matrix_world @ rig.pose.bones[n].head)])
    print('BODYPROBE', c, json.dumps(pts))
