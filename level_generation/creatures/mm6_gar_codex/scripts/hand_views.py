import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_gar.blend'));rig=bpy.data.objects['Rig'];obj=bpy.data.objects['Gargoyle'];scene=bpy.context.scene;report={}
for clip,t in [('Flight',0),('Attack',.75),('Attack',.90),('Attack',1.125),('Hit',.16)]:
 rig.animation_data.action=bpy.data.actions[clip];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(round(t*120));ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();report[f'{clip}:{t}']={}
 for side in ['L','R']:
  ids=[v.index for v in obj.data.vertices if sum(g.weight for g in v.groups if any(s in obj.vertex_groups[g.group].name for s in [f'B_{side}_Hand',f'B_{side}_Finger']))>.8];centre=(co[ids].min(0)+co[ids].max(0))/2;report[f'{clip}:{t}'][side]=[float(centre[0]),float(centre[2]),float(-centre[1])]
(P/'review/attack_v3/posed_centres.json').write_text(json.dumps(report,indent=2));print('POSED_HAND_CENTRES',report)
