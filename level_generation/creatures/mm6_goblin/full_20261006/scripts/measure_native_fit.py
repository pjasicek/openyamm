import bpy,json
from pathlib import Path
from mathutils import Vector
O=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');bpy.ops.wm.open_mainfile(filepath=str(O/'delivery/mm6_goblin.blend'));a=bpy.data.objects['Goblin_Rig'];s=bpy.data.objects['Goblin_Sword'];tip=min(s.data.vertices,key=lambda v:v.co.y);base=a.data.bones['RightHand'].head_local;print('Rest tip vector',tuple(tip.co-base),'length',(tip.co-base).length,'vertex',tip.index,flush=True)
spec=json.loads((O.parent/'stage1_20261006/motion_spec.json').read_text());report=[]
for c in spec['clips']:
 action=bpy.data.actions[c['name']];a.animation_data.action=action;a.animation_data.action_slot=action.slots[0]
 for i,anchor in enumerate(c['anchors']):
  bpy.context.scene.frame_set(1+int(anchor['time_ms']*.192));ev=s.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
  t=ev.vertices[tip.index].co;w=a.pose.bones['RightHand'].head
  project=lambda v:[177.5+v.x*256/1.65,289-v.z*256/1.65]
  r={'clip':c['name'],'time_ms':anchor['time_ms'],'native_tip':anchor['points_xy'][13],'model_tip':project(t),'native_wrist':anchor['points_xy'][4],'model_wrist':project(w),'max_sword_z':max(v.co.z for v in ev.vertices)};report.append(r);print(r,flush=True)
(O/'review/native_tip_fit_after.json').write_text(json.dumps(report,indent=2)+'\n')
