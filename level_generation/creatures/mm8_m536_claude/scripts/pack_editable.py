import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m536.blend'));rig=bpy.data.objects['Rig'];expected=json.loads((P/'work/rig.json').read_text())['bones'];errors={}
for n,b in expected.items():errors[n]=float(np.abs(np.array(rig.data.bones[n].matrix_local.to_3x3())-b['rot']).max())
assert max(errors.values())<1e-5,max(errors.values())
for n in ['FlameTail_LOD1','FlameTail_LOD2']:bpy.data.objects[n].hide_set(True);bpy.data.objects[n].hide_render=True
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m536.blend'))
(P/'review/rest_frame_gate.json').write_text(json.dumps({'max_matrix_component_error':max(errors.values()),'bones_checked':len(errors),'fitted_hand_frames':'mesh knuckle line; see joint_xray.png'},indent=2)+'\n')
