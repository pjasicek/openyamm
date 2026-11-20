import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_gate_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;names={g.index:g.name for g in body.vertex_groups};rest=np.array([tuple(v.co)for v in body.data.vertices]);edges=np.array([tuple(e.vertices)for e in body.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
def posed():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.array([tuple(v.co)for v in m.vertices]);ev.to_mesh_clear();return a
rig.animation_data.action=bpy.data.actions['Attack'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(105);co=posed();stretch=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(length,1e-6);ix=np.where((rest[edges[:,0],0]>0)&(rest[edges[:,0],2]>1.10))[0]
for e in sorted(ix,key=lambda i:-stretch[i])[:12]:
 print('ARM EDGE',edges[e].tolist(),'stretch',stretch[e],'rest',rest[edges[e]].tolist(),'weights',[{names[g.group]:round(g.weight,3)for g in body.data.vertices[int(i)].groups}for i in edges[e]],flush=True)
for clip in ['Walking','Dead']:
 a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];peaks={s:(-1,0)for s in 'LR'}
 ids={s:[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if names[g.group].startswith((f'B_{s}_Foot',f'B_{s}_Toe')))>.5]for s in 'LR'}
 for f in range(int(a.frame_range[1])+1):
  scene.frame_set(f);co=posed()
  for s in 'LR':
   z=co[ids[s],2].min()
   if z>peaks[s][0]:peaks[s]=(z,f)
 for s,(z,f)in peaks.items():
  scene.frame_set(f);co=posed();print('LEG',clip,s,z,f,{n:list(rig.pose.bones[f'B_{s}_{n}'].head)for n in ['Thigh','Calf','Foot','Toe0']},'pelvis',list(rig.pose.bones['B_Pelvis'].head),flush=True)
 if clip=='Dead':
  for region in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Head','B_R_Hand','Staff']:
   ids2=[v.index for v in body.data.vertices if any(names[g.group]==region and g.weight>.5 for g in v.groups)]
   if ids2:print('CORPSE',region,co[ids2,2].min(),co[ids2,2].max(),flush=True)
