import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'review/triangle_reduction/baseline/work/rig_textured.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
for act in bpy.data.actions:
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];vals={sd:[]for sd in 'LR'}
 for i in range(round(act.frame_range[1]/30*48)+1):
  f=i*30/48;sc.frame_set(int(f),subframe=f-int(f))
  for sd in 'LR':
   u=r.pose.bones[f'B_{sd}_UpperArm'];e=r.pose.bones[f'B_{sd}_Forearm'];h=r.pose.bones[f'B_{sd}_Hand'];a=(e.head-u.head).normalized();b=(h.head-e.head).normalized();axis=u.matrix.to_3x3().col[2].normalized();bend=math.degrees(math.atan2(axis.dot(a.cross(b)),a.dot(b)));off=math.degrees(math.asin(max(-1,min(1,axis.dot(b)))));roll=math.degrees(e.rotation_quaternion.to_swing_twist('Y')[1]);vals[sd].append((bend,off,roll))
 print('ANATOMY',act.name,{sd:[(min(v[k]for v in val),max(v[k]for v in val))for k in range(3)]for sd,val in vals.items()})
