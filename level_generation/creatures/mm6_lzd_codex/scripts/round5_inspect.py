import bpy,json,sys,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/near_runtime.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene
pv=np.array([x.value for x in o.data.attributes['piece'].data])
parts={}
for pid in sorted(set(pv.tolist())):
 vs=[v for v in o.data.vertices if pv[v.index]==pid];a=np.array([v.co[:] for v in vs]);w={}
 for v in vs:
  for g in v.groups:w[o.vertex_groups[g.group].name]=w.get(o.vertex_groups[g.group].name,0)+g.weight/len(vs)
 parts[str(pid)]={'n':len(vs),'min':a.min(0).tolist(),'max':a.max(0).tolist(),'weights':dict(sorted(w.items(),key=lambda kv:-kv[1])[:5])}
trace={}
for clip in ['Standing','Walking','Running']:
 act=bpy.data.actions[clip];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];rows=[]
 for t in np.linspace(0,(act.frame_range[1]-act.frame_range[0])/30,49):
  f=t*30;sc.frame_set(int(f),subframe=f%1);row={'time':t}
  for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2']:
   D=r.pose.bones[n].matrix.to_3x3()@r.data.bones[n].matrix_local.to_3x3().inverted()
   row[n]=math.degrees(math.atan2(D[1][0],D[0][0]))
  rows.append(row)
 trace[clip]=rows
(P/'review/round5/inspection.json').write_text(json.dumps({'parts':parts,'yaw':trace},indent=2))
print(json.dumps({'parts':parts,'walk_tail':trace['Walking'][-8:]},indent=2))
