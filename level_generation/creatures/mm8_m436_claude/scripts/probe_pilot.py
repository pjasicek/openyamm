from pathlib import Path
import bpy,numpy as np,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_fitted.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Attack'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(21);m=b.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();co=np.array([tuple(v.co) for v in b.data.vertices]);x=np.array([tuple(v.co) for v in m.vertices]);edges=np.array([tuple(e.vertices) for e in b.data.edges]);stretch=np.linalg.norm(x[edges[:,0]]-x[edges[:,1]],axis=1)/np.maximum(1e-6,np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1));ix=np.argsort(-stretch)[:15];report=[]
for e in ix:
 row=[]
 for i in edges[e]:
  v=b.data.vertices[int(i)];row.append({'v':int(i),'rest':list(v.co),'pose':x[i].tolist(),'piece':b.data.attributes['piece'].data[int(i)].value,'weights':{b.vertex_groups[w.group].name:w.weight for w in v.groups}})
 report.append({'stretch':float(stretch[e]),'verts':row})
print(json.dumps(report,indent=1));(p/'work/pilot_stretch_probe.json').write_text(json.dumps(report,indent=2))
for n in ['B_Head','B_L_Foot','B_L_Toe0','B_R_Foot','B_R_Toe0']:print('BONE',n,tuple(r.data.bones[n].head_local),tuple(r.data.bones[n].tail_local))

import sys
sys.path.insert(0,str(p/'scripts'));import common
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/attack_repair'),1.1,1.35,views=('front','three_quarter','back'),resolution=(640,640))
