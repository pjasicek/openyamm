"""Both fists in an action: angle between the left and right grip axes (grip_pose_L/grip_pose, hand space) and the right
grip's position in the left grip's frame (y along the shaft). Args: -- <blend> <action>"""
import bpy, sys, os, json, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, an = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
GL = json.load(open(os.path.join(common.WORK, 'grip_pose_L.json'))); GR = json.load(open(os.path.join(common.WORK, 'grip_pose.json')))
act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 3):
    sc.frame_set(f)
    HL = rig.matrix_world @ rig.pose.bones['B_L_Hand'].matrix; HR = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
    aL = (HL.to_3x3().normalized() @ Vector(GL['handle_axis_hand_local'])).normalized()
    aR = (HR.to_3x3().normalized() @ Vector(GR['handle_axis_hand_local'])).normalized()
    cL = HL @ Vector(GL['handle_centre_hand_local']); cR = HR @ Vector(GR['handle_centre_hand_local'])
    d = cR - cL
    print('GRIPS', f, 'axis angle', round(math.degrees(aL.angle(aR)), 1), 'R along L axis', round(d.dot(aL), 3),
          'off-axis', round((d - aL * d.dot(aL)).length, 3), 'L axis', [round(x, 2) for x in aL])
