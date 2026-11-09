"""Bow-arm geometry of a clip frame: shoulder, elbow, wrist, forearm and hand axes, bow axes and grip, the grip frame
(bow axes in the hand), arm lengths. Usage: blender -b -P carry_probe.py -- <master.blend> <action> <frames,comma>"""
import bpy, sys, json, math
from mathutils import Vector, Matrix
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0]); sc = bpy.context.scene; rig = bpy.data.objects['Rig']; pb = rig.pose.bones
rig.animation_data.action = bpy.data.actions[args[1]]; rig.animation_data.action_slot = rig.animation_data.action.slots[0]
r = lambda v: [round(x, 3) for x in v]
P = bpy.path.abspath('//'); G = json.load(open(P + 'equipment.json'))
hr = Matrix(G['rest_hand_matrix']).to_3x3(); br = Matrix(G['bow_rest_matrix']).to_3x3()
g = hr.inverted() @ br
print('GRIP bow axes in hand frame: limbs', r(g.col[1]), 'string', r(-g.col[2]), 'normal', r(g.col[0]),
      'centre_hand_local', r(G['centre_hand_local']))
print('LEN arm', round(pb['LArm'].length, 3), 'fore', round(pb['LForeArm'].length, 3), 'hand', round(pb['LHand'].length, 3))
rb = rig.data.bones
print('REST bow in hand frame', r((rb['LHand'].matrix_local.to_3x3().inverted() @ rb['Bow'].matrix_local.to_3x3()).col[1]))
for f in (int(x) for x in args[2].split(',')):
    sc.frame_set(f)
    fa = (pb['LForeArm'].tail - pb['LForeArm'].head).normalized(); h = (pb['LHand'].tail - pb['LHand'].head).normalized()
    B = pb['Bow'].matrix.to_3x3().normalized()
    print('F', f, 'sh', r(pb['LArm'].head), 'el', r(pb['LForeArm'].head), 'wr', r(pb['LHand'].head), 'fa', r(fa), 'hand', r(h),
          'bend', round(math.degrees(fa.angle(h)), 1), 'bow_c', r(pb['Bow'].head), 'limbs', r(B.col[1]), 'string', r(-B.col[2]),
          'fa_vs_limbs', round(math.degrees(fa.angle(B.col[1])), 1))
