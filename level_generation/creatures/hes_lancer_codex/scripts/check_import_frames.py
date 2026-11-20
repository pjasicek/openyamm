"""Check that source-frame calibration survives the glTF import before retargeting."""
import json
from pathlib import Path
import bpy

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P.with_name('hes_kreegan_claude') / 'work/rig_v3t.blend'))
rest = {b.name: b.matrix_local.copy() for b in bpy.data.objects['Rig'].data.bones}
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/clear_v2.blend'))
rig = bpy.data.objects['Rig']
for name in ('B_Pelvis', 'B_Spine', 'B_L_Thigh', 'B_R_Thigh', 'B_L_Calf', 'B_R_Calf', 'B_L_Foot', 'B_R_Foot'):
    b = rig.data.bones[name]
    print('REST', name, 'angle', rest[name].to_quaternion().rotation_difference(b.matrix_local.to_quaternion()).angle,
          'translation', (rest[name].translation - b.matrix_local.translation).length)
for name in ('Carbine_Standing', 'Running', 'Lancer_Running'):
    a = bpy.data.actions[name]
    rig.animation_data.action = a
    rig.animation_data.action_slot = a.slots[0]
    for f in (0, 5, 10, 15, 20):
        bpy.context.scene.frame_set(f)
        print('POSE', name, f, {n: [round(v, 3) for v in rig.pose.bones[n].head] for n in
              ('B_Pelvis', 'B_L_Hand', 'B_L_Thigh', 'B_L_Calf', 'B_L_Foot', 'B_R_Thigh', 'B_R_Calf', 'B_R_Foot')})
