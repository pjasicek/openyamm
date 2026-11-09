"""Distance and offset between the right and left grip tunnel centres per clip (in the right tunnel's rifle frame
guess: barrel = right -> left). Args: -- <blend> <clip> [...]"""
import bpy, sys, os, json, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
GR = json.load(open(os.path.join(HERE, 'work', 'grip_pose_R.json'))); GL = json.load(open(os.path.join(HERE, 'work', 'grip_pose_L.json')))
cR, cL = Vector(GR['handle_centre_hand_local']), Vector(GL['handle_centre_hand_local'])
aR = Vector(GR['handle_axis_hand_local'])
for c in a[1:]:
    act = bpy.data.actions[c]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); ds = []; ang = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        HR = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix; HL = rig.matrix_world @ rig.pose.bones['B_L_Hand'].matrix
        pR, pL = HR @ cR, HL @ cL; v = pL - pR; ds.append(v.length)
        g = (HR.to_3x3() @ aR).normalized(); ang.append(math.degrees(g.angle(v)))
    print('HANDS', c, 'dist min/mean/max', round(min(ds), 3), round(sum(ds) / len(ds), 3), round(max(ds), 3),
          'grip axis to the hand line deg', round(min(ang), 1), round(max(ang), 1))
