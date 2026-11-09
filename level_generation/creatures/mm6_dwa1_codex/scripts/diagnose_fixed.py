import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_fixed.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data
co=np.array([tuple(v.co)for v in me.vertices]);E=np.array([tuple(e.vertices)for e in me.edges]);rl=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);pv=np.array([a.value for a in me.attributes['piece'].data]);gn={g.index:g.name for g in ob.vertex_groups}
common.workbench_clay(bpy.context.scene)
for n,f in [('Standing',0),('Walking',6),('Attack',20),('Attack',32),('Fidget',8),('Death',20)]:
 a=bpy.data.actions[n];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();cc=np.array([tuple(v.co)for v in m.vertices]);ev.to_mesh_clear();r=np.linalg.norm(cc[E[:,0]]-cc[E[:,1]],axis=1)/np.maximum(rl,1e-6)
 print('PARTSTRETCH',n,f,[(int(p),round(float(np.percentile(r[pv[E[:,0]]==p],99)),2))for p in range(14)])
 for idx in np.argsort(-r)[:8]:
  e=E[idx];print('WORST',float(r[idx]),[(int(i),int(pv[i]),list(np.round(co[i],4)),[(gn[g.group],round(g.weight,3))for g in me.vertices[i].groups if g.weight>.001])for i in e])
 common.render_views(str(P/f'review/fixed_{n}_{f}'),.65,1.7,views=('front','left'),resolution=(360,500))
