import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; AW = rig.matrix_world
FR = json.load(open(os.path.join(HERE, 'work', 'rifle_frame.json'))); HG_Z = FR['left_centre_rifle'][2]
GL = json.load(open(os.path.join(HERE, 'work', 'grip_pose_L.json'))); cL = Vector(GL['handle_centre_hand_local'])
for c in a[1:]:
    act = bpy.data.actions[c]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    for f in (0, 10):
        sc.frame_set(f)
        Rw = AW @ rig.pose.bones['Rifle'].matrix; Hn = AW @ rig.pose.bones['B_L_Hand'].matrix
        cc = Rw.inverted() @ (Hn @ cL)
        S = (AW @ rig.pose.bones['B_L_UpperArm'].matrix).translation; E = (AW @ rig.pose.bones['B_L_Forearm'].matrix).translation
        Wp = Hn.translation
        print('DBG', c, f, 'tunnel in rifle', [round(x, 3) for x in cc], 'shoulder-wrist', round((Wp - S).length, 3), 'L1', round((E - S).length, 3), 'L2', round((Wp - E).length, 3),
              'hand scale', [round(x, 3) for x in Hn.to_scale()])
