import bpy,json
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_final.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];s=bpy.context.scene;piece=np.array([x.value for x in b.data.attributes['piece'].data]);out={}
for name in ('Death','Dead'):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];out[name]=[]
 for f in range(0,int(a.frame_range[1])+1,6):
  s.frame_set(f);e=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();co=np.array([v.co[:] for v in m.vertices]);e.to_mesh_clear();out[name].append({'frame':f,'floors':{int(k):round(float(co[piece==k,2].min()),4) for k in np.unique(piece)}})
print('PART_FLOORS',json.dumps(out));(p/'work/floor_probe.json').write_text(json.dumps(out,indent=2))
