import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5.blend'))
o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=o.data
co=np.array([v.co[:] for v in me.vertices]);edges=np.array([e.vertices[:] for e in me.edges]);rl=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)
pv=[a.value for a in me.attributes['piece'].data];gn=[g.name for g in o.vertex_groups]
for act,frame in [('Standing',0),('Attack',26),('Death',94)]:
 rig.animation_data.action=bpy.data.actions[act];rig.animation_data.action_slot=bpy.data.actions[act].slots[0];bpy.context.scene.frame_set(frame)
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();pose=np.array([v.co[:] for v in em.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(pose[edges[:,0]]-pose[edges[:,1]],axis=1)/np.maximum(rl,1e-7)
 for i in np.argsort(ratio)[-12:][::-1]:
  print(act,frame,'ratio',round(ratio[i],2),'rest_mm',round(rl[i]*1000,2),'piece',pv[edges[i,0]],[(int(v),co[v].round(3).tolist(),[(gn[g.group],round(g.weight,3)) for g in me.vertices[v].groups if g.weight>.03]) for v in edges[i]])
