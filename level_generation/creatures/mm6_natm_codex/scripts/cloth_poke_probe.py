import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/contact_master.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(61);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pt=np.array([-.163117893,.286288157,.07808837]);pv=[d.value for d in ob.data.attributes['piece'].data];vv=np.array([tuple(v.co)for v in me.vertices]);ev.to_mesh_clear();ids=sorted([v.index for v in ob.data.vertices if pv[v.index]==10],key=lambda i:np.linalg.norm(vv[i]-pt))[:8]
for i in ids:print('POKE NEAR',i,'rest',list(ob.data.vertices[i].co),'posed',vv[i].tolist(),'w',[(ob.vertex_groups[g.group].name,g.weight)for g in ob.data.vertices[i].groups],flush=True)
for f in [59,60,61,62,63]:
 bpy.context.scene.frame_set(f);print('ROOT',f,list(rig.pose.bones['ClothBack'].rotation_quaternion),flush=True)
