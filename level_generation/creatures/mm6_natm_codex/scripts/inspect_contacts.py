import bpy,sys,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for blend in ['textured_master','cloth_master','contact_master']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{blend}.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(92);pv=np.array([d.value for d in body.data.attributes['piece'].data]);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vv=np.array([tuple(v.co)for v in me.vertices]);ev.to_mesh_clear();print('BLEND',blend,flush=True)
 for part in [0,1,10]:
  ids=np.where(pv==part)[0];print('PART',part,'bounds',vv[ids].min(0),vv[ids].max(0),flush=True)
  if part!=0:
   for i in sorted(ids,key=lambda i:vv[i,2])[:4]:print('LOW',int(i),'rest',list(body.data.vertices[i].co),'posed',vv[i].tolist(),'weights',[(body.vertex_groups[g.group].name,g.weight)for g in body.data.vertices[i].groups],flush=True)
 for n in ['B_Pelvis','B_L_Thigh','B_L_Calf','B_R_Hand','Spear','ClothFront','ClothBack','ClothBack1','ClothBack2','ClothBack3']:
  if n in rig.pose.bones:
   pb=rig.pose.bones[n];print('BONE',n,'loc',list(pb.location),'head',list(pb.head),'q',list(pb.rotation_quaternion),'scale',list(pb.scale),flush=True)
