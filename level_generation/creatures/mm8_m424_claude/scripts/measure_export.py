import bpy, json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/m424_textured_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['M424'];sc=bpy.context.scene
report={}
for name in ['Standing','Walking','Running']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];feet=[];heights=[]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(v.co) for v in me.vertices]);heights.append(float(co[:,2].max()-co[:,2].min()));ev.to_mesh_clear()
  feet.append([tuple(rig.pose.bones['B_'+s+'_Foot'].matrix.translation) for s in 'LR'])
 feet=np.array(feet);vs=[]
 for side in range(2):
  z=feet[:,side,2];vy=np.gradient(feet[:,side,1])*60;vs.append(float(np.median(vy[z<z.min()+.01])))
 report[name]={'duration':float(a.frame_range[1]/60),'height_first':heights[0],'height_range':[min(heights),max(heights)],'stride':float(np.mean(vs)*a.frame_range[1]/60)}
(P/'work/runtime_measurements.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
