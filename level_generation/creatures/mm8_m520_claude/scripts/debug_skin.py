from pathlib import Path
import bpy,numpy as np
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_fitted.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(24)
names=[b.name for b in rig.data.bones];pose_names=[b.name for b in rig.pose.bones];print('ORDERS_MATCH',names==pose_names,[(i,x,pose_names[i]) for i,x in enumerate(names) if x!=pose_names[i]])
print('OBJECT_MATRICES',rig.matrix_world[:],body.matrix_world[:])
idx={n:i for i,n in enumerate(names)};rest=np.array([rig.data.bones[n].matrix_local for n in names]);base=np.array([rig.pose.bones[n].matrix for n in names]);co=np.array([v.co[:] for v in body.data.vertices]);w=np.zeros((len(co),len(names)))
for v in body.data.vertices:
 for g in v.groups:w[v.index,idx[body.vertex_groups[g.group].name]]=g.weight
posed=np.einsum('vj,jab,vb->va',w,base@np.linalg.inv(rest),np.c_[co,np.ones(len(co))])[:,:3]
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();actual=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();error=np.linalg.norm(actual-posed,axis=1)
print('LBS_ERROR',error.max(),np.argmax(error),np.percentile(error,[50,90,99]));print('MODIFIERS',[(m.name,m.type,getattr(m,'use_deform_preserve_volume',None)) for m in body.modifiers])
