import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
for name in ['rig_final_textured','production_master']:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work'/f'{name}.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 prev=None
 for f in [8,8.5,9,10,11,11.5,12,12.5,13]:
  bpy.context.scene.frame_set(int(f),subframe=f-int(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=min(m.vertices,key=lambda x:x.co.z);original=body.data.vertices[v.index]
  print(name,f,'low',v.index,list(v.co),'weights',[(body.vertex_groups[g.group].name,round(g.weight,3)) for g in original.groups])
  ev.to_mesh_clear()
 bpy.context.scene.frame_set(11);q0={b.name:b.rotation_quaternion.copy() for b in rig.pose.bones}
 bpy.context.scene.frame_set(12)
 for b in rig.pose.bones:
  if q0[b.name].dot(b.rotation_quaternion)<.95:print('NEGATIVE',name,b.name,q0[b.name][:],b.rotation_quaternion[:])
