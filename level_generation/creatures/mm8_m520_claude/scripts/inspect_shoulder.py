from pathlib import Path
import bpy,numpy as np,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_weighted.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(18)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();rows=[]
for v in body.data.vertices:
 if .24<v.co.x<.52 and v.co.z>1.79:
  rows.append({'i':v.index,'rest':list(v.co),'pose':list(mesh.vertices[v.index].co),'weights':[(body.vertex_groups[g.group].name,round(g.weight,3)) for g in v.groups if g.weight>.01]})
print(json.dumps(sorted(rows,key=lambda r:r['pose'][0],reverse=True)[:20],indent=1),flush=True)
for n in ['B_L_Clavicle','B_L_UpperArm','B_L_UpperArmTwist','B_L_Forearm','B_L_Hand']:
 b=rig.pose.bones[n];print('BONE',n,'head',list(b.head),'local',list(b.rotation_quaternion),'loc',list(b.location),'scale',list(b.scale),flush=True)
ev.to_mesh_clear()
