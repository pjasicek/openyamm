"""Measure stride from the planted shoe and wooden peg, excluding swing and flight."""
import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_settled.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
pc=np.array([a.value for a in body.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in body.data.vertices]);masks=[(pc==6)&(rest[:,2]<.04),(pc==12)&(rest[:,2]<.04)];report={}
for name in ['Walking','Running']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[];times=np.arange(0,float(a.frame_range[1])+.001,.25)
 for f in times:
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([(body.matrix_world@v.co)[:] for v in me.vertices]);ev.to_mesh_clear();rows.append([[float(co[m,2].min()),float(np.median(co[m,1]))] for m in masks])
 data=np.array(rows);dt=1/120;vel=np.gradient(data[:,:,1],dt,axis=0);duration=float(a.frame_range[1])/30;result={}
 for height in [.005,.01,.02]:
  planted=(data[:,:,0]<height)&(vel>0);values=vel[planted];assert len(values)>8
  result[str(height)]={'speed':float(np.median(values)),'stride':float(np.median(values)*duration),'samples':len(values),'feet':[float(np.median(vel[:,i][planted[:,i]])) for i in range(2)]}
 report[name]=result;print('PHYSICAL_STRIDE',name,result,flush=True)
(P/'work/physical_stride.json').write_text(json.dumps(report,indent=2)+'\n')
