from pathlib import Path
import bpy,json
import numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_animated.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=o.data;co=np.array([tuple(v.co) for v in me.vertices]);e=np.array([tuple(x.vertices) for x in me.edges]);rl=np.linalg.norm(co[e[:,0]]-co[e[:,1]],axis=1);pv=np.array([a.value for a in me.attributes['piece'].data]);cr=np.array([a.value for a in me.attributes['cloth_region'].data]);report={}
for name,f in [('Attack',31),('Death',17),('Hit',7)]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();pos=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(pos[e[:,0]]-pos[e[:,1]],axis=1)/np.maximum(rl,1e-6)
 rows=[]
 for region in [0,2,3,4]:
  mask=(cr[e[:,0]]==region)&(cr[e[:,1]]==region)&(rl>.0005)
  if region==0:mask&=(pv[e[:,0]]==0)&(abs(co[e[:,0],0])>.14)&(co[e[:,0],2]>1.06)
  inds=np.where(mask)[0];inds=inds[np.argsort(-ratio[inds])[:5]]
  for i in inds:rows.append({'region':region,'ratio':float(ratio[i]),'vertices':e[i].tolist(),'rest':co[e[i]].tolist(),'weights':[[[o.vertex_groups[g.group].name,round(g.weight,3)] for g in me.vertices[j].groups if g.weight>.01] for j in e[i]]})
 report[name]=rows
(p/'work/edge_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
