import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Attack'];C=np.array([v.co[:] for v in b.data.vertices]);E=np.array([e.vertices[:] for e in b.data.edges]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1);best=[]
for f in range(1,47):
 bpy.context.scene.frame_set(f);o=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=o.to_mesh();c=np.array([v.co[:] for v in m.vertices]);o.to_mesh_clear();s=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1)/np.maximum(EL,1e-8)
 for i in np.argsort(s)[-3:]:
  best.append({'frame':f,'stretch':float(s[i]),'vertices':[{'id':int(v),'co':C[v].tolist(),'weights':{b.vertex_groups[g.group].name:g.weight for g in b.data.vertices[v].groups}} for v in E[i]]})
best=sorted(best,key=lambda x:-x['stretch'])[:12];(P/'review/stretch_probe.json').write_text(json.dumps(best,indent=2));print(json.dumps(best[:4]))
