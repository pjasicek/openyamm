import bpy,math,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_contacts.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;b=bpy.data.objects['Body'];me=b.data;rest=np.array([v.co[:] for v in me.vertices]);E=np.array([e.vertices[:] for e in me.edges]);rl=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1);a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for f in [0,8,10,12,14,16,18,24]:
 sc.frame_set(f);report={}
 for s in 'RL':
  U,F,H=[r.pose.bones[f'B_{s}_{n}'].head for n in ['UpperArm','Forearm','Hand']];report[s]=math.degrees((F-U).angle(H-F))
 print('ELBOW_FLEX',f,report)
 if f==12:
  ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(v[E[:,0]]-v[E[:,1]],axis=1)/np.maximum(rl,1e-8)
  for k in np.argsort(ratio)[-15:]:print('EDGE',ratio[k],[(int(i),rest[i].tolist(),{b.vertex_groups[g.group].name:round(g.weight,3) for g in me.vertices[i].groups}) for i in E[k]])
