import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_twist.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene;common.workbench_clay(scene)
E=np.array([tuple(e.vertices)for e in me.edges]);R=np.array([tuple(v.co)for v in me.vertices]);rl=np.linalg.norm(R[E[:,0]]-R[E[:,1]],axis=1)
for nm,frames in [('Attack',[0,7,10,12,24,31,35,38,44]),('Standing',[0]),('Hit',[4]),('Death',[8,31]),('Walking',[0,12]),('Cast',[18])]:
 a=bpy.data.actions[nm];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in frames:
  scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(v.co)for v in m.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1)/np.maximum(rl,1e-6)
  print('WORST',nm,f,[(float(ratio[k]),[{'v':int(i),'rest':R[i].tolist(),'part':me.attributes['piece'].data[int(i)].value,'weights':[(body.vertex_groups[g.group].name,round(g.weight,2))for g in me.vertices[int(i)].groups if g.weight>.01]}for i in E[k]])for k in np.argsort(ratio)[-3:]])
  common.render_views(str(P/f'review/pose_{nm}_{f:02d}'),.88,2.05,views=('front','left','three_quarter'),resolution=(300,440))
