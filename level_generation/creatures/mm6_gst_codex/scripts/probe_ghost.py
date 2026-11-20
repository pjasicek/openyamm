import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot_v1.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];C=np.array([v.co[:] for v in o.data.vertices]);E=np.array([e.vertices[:] for e in o.data.edges]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1)
for role,frame in [('Death',58),('Attack',49)]:
 r.animation_data.action=bpy.data.actions[role];bpy.context.scene.frame_set(frame);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();length=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1);ids=np.argsort(length-EL)[-5:]
 for i in ids:
  print(role,'EDGE',E[i],C[E[i]].round(3).tolist(),'eval',c[E[i]].round(3).tolist(),'mm',round(EL[i]*1000,1),round(length[i]*1000,1))
  for v in E[i]:print([(o.vertex_groups[g.group].name,round(g.weight,3)) for g in o.data.vertices[int(v)].groups if g.weight>.01])
