import bpy
import json
import numpy as np
from pathlib import Path

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation')
scene=bpy.data.scenes['MM6_Demon_Attack']
bpy.context.window.scene=scene
rig=scene.objects['Demon_Attack_Rig'];obj=scene.objects['Demon_Attack_Mesh']
action=bpy.data.actions['Demon_Native_Attack']
rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
data=np.load(stage/'source_geometry.npz');rest,faces=data['vertices'],data['faces']
original_area=np.linalg.norm(np.cross(rest[faces[:,1]]-rest[faces[:,0]],rest[faces[:,2]]-rest[faces[:,0]]),axis=1)
worst={};pose_vertices=[];basis=[];angles=[];previous=None;markers=[]
for time in np.arange(0,36.01,.25):
 scene.frame_set(int(time),subframe=float(time%1))
 evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
 v=np.array([tuple(vertex.co) for vertex in mesh.vertices]);evaluated.to_mesh_clear()
 area=np.linalg.norm(np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]]),axis=1)/original_area
 for index in np.flatnonzero(area<.1):
  if int(index) not in worst or area[index]<worst[int(index)]['ratio']:
   face=faces[index];ws=data['weights'][face].mean(0);columns=np.argsort(ws)[-3:]
   worst[int(index)]={'triangle':int(index),'frame':float(time),'ratio':float(area[index]),
     'original_area':float(original_area[index]/2),'center':rest[face].mean(0).tolist(),
     'vertices':face.tolist(),'groups':[(str(data['group_names'][j]),float(ws[j])) for j in columns]}
 quats={b.name:b.matrix.to_quaternion() for b in rig.pose.bones}
 if previous:
  for name,q in quats.items():
   delta=2*np.arccos(min(1,abs(previous[name].dot(q))))*180/np.pi
   angles.append({'bone':name,'frame':float(time),'degrees':float(delta)})
 previous=quats
 if time%1==0:
  pose_vertices.append(v)
  basis.append([np.array(b.matrix_basis) for b in rig.pose.bones])
  markers.append({b.name:list(b.head) for b in rig.pose.bones})
np.savez_compressed(stage/'attack_pose_arrays.npz',vertices=np.array(pose_vertices),basis=np.array(basis),
                    times=np.arange(37)/48,bone_names=np.array([b.name for b in rig.pose.bones]))
(stage/'pose_markers.json').write_text(json.dumps(markers)+'\n')
report={'surface_flags':sorted(worst.values(),key=lambda x:x['ratio']),
        'largest_shortest_quaternion_steps':sorted(angles,key=lambda x:x['degrees'],reverse=True)[:12]}
(stage/'surface_flags.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
