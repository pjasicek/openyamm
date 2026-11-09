"""Which end of the fist the handle axis (+Y of the Sword frame, toward the blade) leaves: the dot of the axis with the
direction from the handle centre to the thumb base / to the pinky knuckle (rest hand). Args: -- <blend>"""
import bpy, sys, os, json
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1]); rig = bpy.data.objects['Rig']
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
Hm = rig.data.bones['B_R_Hand'].matrix_local
c = Hm @ Vector(G['handle_centre_hand_local']); ax = (Hm.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
th = rig.data.bones['B_R_Finger0'].head_local; pk = rig.data.bones['B_R_Finger4'].head_local; ix = rig.data.bones['B_R_Finger1'].head_local
print('AXISSIDE to thumb base', round(ax.dot((th - c).normalized()), 2), 'to index knuckle', round(ax.dot((ix - c).normalized()), 2),
      'to pinky knuckle', round(ax.dot((pk - c).normalized()), 2))
