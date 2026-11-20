import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_fitted.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;report=json.loads((P/'review/rig_gates.json').read_text());me=b.data;co=np.array([v.co[:] for v in me.vertices]);E=np.array([e.vertices[:] for e in me.edges]);length=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);out={}
def weights(i):return {b.vertex_groups[g.group].name:round(g.weight,3) for g in me.vertices[i].groups}
for nm in ['Attack','Cast','Fidget']:
 out[nm]={};a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for s,v in report[nm]['G4'].items():
  f=v['frame'];sc.frame_set(int(f),subframe=f%1);e=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();posed=np.array([v.co[:] for v in m.vertices]);e.to_mesh_clear();rat=np.linalg.norm(posed[E[:,0]]-posed[E[:,1]],axis=1)/np.maximum(length,1e-8);mask=np.array([sum(g.weight for g in v.groups if b.vertex_groups[g.group].name.startswith('B_'+s+'_') and any(t in b.vertex_groups[g.group].name for t in ['UpperArm','Forearm','Hand']))>.3 for v in me.vertices]);ids=np.where(mask[E[:,0]]&mask[E[:,1]])[0];ids=ids[np.argsort(rat[ids])[-12:]];out[nm][s+'_stretch']=[{'ratio':float(rat[k]),'vertices':[{'id':int(i),'co':co[i].tolist(),'weights':weights(i)} for i in E[k]]} for k in ids]
 out[nm]['contacts']={k:{**v,'rest_sample':(list(ax.data.vertices[v['sample']].co) if k=='axe' else list(me.vertices[v['sample']].co)) if v['sample'] is not None else None,'body_face':[(list(me.vertices[i].co),weights(i)) for i in v['hit_face']] if v['hit_face'] else None} for k,v in report[nm]['G6'].items() if v['depth_m']>.002}
(P/'review/round1/bad_geometry.json').write_text(json.dumps(out,indent=2))
