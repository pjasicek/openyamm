import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene
co=np.array([v.co[:] for v in o.data.vertices]);E=np.array([e.vertices[:] for e in o.data.edges]);EL=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);names={g.index:g.name for g in o.vertex_groups}
for clip,frame in [('Standing',24),('Attack',28),('Death',36)]:
 r.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();dl=np.linalg.norm(a[E[:,0]]-a[E[:,1]],axis=1)-EL
 print(clip,'worst absolute stretching')
 for e in np.argsort(dl)[-6:]:
  print('edge',int(e),'change',dl[e],'old',EL[e])
  for i in E[e]:print(int(i),co[i].round(5).tolist(),[(names[g.group],round(g.weight,3)) for g in o.data.vertices[i].groups])
