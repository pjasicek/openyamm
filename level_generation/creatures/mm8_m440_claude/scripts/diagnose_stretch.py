from pathlib import Path
import bpy,numpy as np,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'));b=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=b.data
rest=np.array([tuple(v.co) for v in me.vertices]);edges=np.array([tuple(e.vertices) for e in me.edges]);parts=np.array([a.value for a in me.attributes['piece'].data]);gn=[g.name for g in b.vertex_groups];w=np.array([sum(e.weight for e in v.groups if gn[e.group].startswith(('B_R_UpperArm','B_R_Forearm','B_R_Hand'))) for v in me.vertices]);mask=(w[edges]>.3).all(1);ix=edges[mask];length=np.linalg.norm(rest[ix[:,0]]-rest[ix[:,1]],axis=1);report={}
for name,f in [('Attack',24.375),('Running',1.875),('Fidget',11.875)]:
 rig.animation_data.action=bpy.data.actions[name];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(int(f),subframe=f-int(f));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(co[ix[:,0]]-co[ix[:,1]],axis=1)/np.maximum(length,1e-8);worst=[]
 for k in np.argsort(ratio)[-30:][::-1]:
  v=int(ix[k,0]);worst.append({'ratio':float(ratio[k]),'piece':int(parts[v]),'position':rest[v].tolist(),'weights':{gn[e.group]:e.weight for e in me.vertices[v].groups}})
 report[name]=worst;print('STRETCH',name,[(round(q['ratio'],2),q['piece'],[round(x,3) for x in q['position']]) for q in worst[:10]])
(p/'work/stretch_locations.json').write_text(json.dumps(report,indent=2))
