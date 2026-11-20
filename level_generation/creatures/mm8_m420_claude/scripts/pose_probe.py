from pathlib import Path
import bpy,numpy as np,json
P=Path(__file__).resolve().parents[1]
for file in ['equipped','grounded']:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work'/(file+'.blend')));rig=bpy.data.objects['Rig'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in [0,10,20,30,39]:
  bpy.context.scene.frame_set(f);row={'f':f}
  for n in ['Body','StaffMesh']:
   o=bpy.data.objects[n];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=np.array([(o.matrix_world@v.co)[:] for v in m.vertices]);ev.to_mesh_clear();row[n]=[c.min(0).tolist(),c.max(0).tolist()]
  for n in ['B_Pelvis','B_R_UpperArm','B_R_Forearm','B_R_Hand','B_Head']:row[n]=(rig.matrix_world@rig.pose.bones[n].head)[:]
  print('PROBE',file,json.dumps(row))
