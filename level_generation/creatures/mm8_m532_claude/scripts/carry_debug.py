"""Debug the carry solve on one frame: the penalty terms of the cheapest and the straightest candidates.
Usage: blender -b -P carry_debug.py -- <blend> <action> <frame>"""
import bpy, sys, json, math
from pathlib import Path
import numpy as np
from mathutils import Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent)); import carry
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); sc = bpy.context.scene; rig = bpy.data.objects['Rig']; pb = rig.pose.bones
rig.animation_data.action = bpy.data.actions[a[1]]; rig.animation_data.action_slot = rig.animation_data.action.slots[0]; sc.frame_set(int(a[2]))
P = Path(__file__).resolve().parents[1]; G = json.loads((P / 'work/equipment.json').read_text())
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
out, up, fwd = carry.body_axes(rig, rest); S = pb['LArm'].head; B = pb['Bow'].matrix.copy()
print('DBG shoulder', [round(x, 3) for x in S], 'bow c', [round(x, 3) for x in B.translation], 'dist', round((B.translation - S).length, 3),
      'reach', round(pb['LArm'].length + pb['LForeArm'].length, 3), 'out', [round(x, 2) for x in out], 'up', [round(x, 2) for x in up],
      'limbs', [round(x, 2) for x in B.to_3x3().col[1]])
grip = Matrix(G['rest_hand_matrix']).to_3x3().inverted() @ Matrix(G['bow_rest_matrix']).to_3x3()
for fz in (-1, .08):
    H, W, E, bend, cost = carry.solve(S, pb['LArm'].length, pb['LForeArm'].length, B, grip, G['centre_hand_local'], out, up, fwd, None, fz)
    rel = E - S
    print('DBG floor', fz, 'bend', round(bend, 1), 'cost', round(cost, 1), 'E', [round(x, 3) for x in E], 'W', [round(x, 3) for x in W],
          'el_below_sh', round(-rel.dot(up), 3), 'el_out', round(rel.dot(out), 3), 'el_fwd', round(rel.dot(fwd), 3))
