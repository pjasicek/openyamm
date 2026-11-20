import bpy,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v6.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];co=np.array([tuple(v.co) for v in b.data.vertices]);E=np.array([tuple(e.vertices) for e in b.data.edges]);rl=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);names=[g.name for g in b.vertex_groups]
for nm,f in [('Attack',17),('Hit',8),('Death',27),('Death',12)]:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear();rat=np.linalg.norm(v[E[:,0]]-v[E[:,1]],axis=1)/np.maximum(rl,1e-8);rows=[]
 for ei in np.argsort(rat)[::-1]:
  va,vb=E[ei];ws={names[g.group]:g.weight for g in b.data.vertices[va].groups};arm=sum(x for n,x in ws.items() if n.startswith('B_R_') and any(k in n for k in ['Forearm','UpperArm','Hand']))
  if arm<.3:continue
  rows.append({'stretch':float(rat[ei]),'a':int(va),'b':int(vb),'rest':co[va].tolist(),'weights':sorted(ws.items(),key=lambda x:-x[1])[:3]})
  if len(rows)==12:break
 print(nm,rows,flush=True)
