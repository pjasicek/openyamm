"""Damp the source fall's neck snap for the heavier horned head; retain endpoints and duration."""
from pathlib import Path
import bpy,numpy as np,json,runpy,sys
from mathutils import Quaternion
p=Path(__file__).resolve().parents[1];names=['B_Neck','B_Head'];kernel=np.array([1,4,6,4,1],float)/16
bpy.ops.wm.open_mainfile(filepath=str(p/'work/hands.blend'));rig=bpy.data.objects['Rig'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
q={n:[] for n in names}
for f in range(int(a.frame_range[1])+1):
 bpy.context.scene.frame_set(f)
 for n in names:q[n].append(np.array(rig.pose.bones[n].rotation_quaternion))
if not a.get('m488_neck_filtered'):
 for n in names:
  arr=np.array(q[n])
  for i in range(1,len(arr)):
   if arr[i]@arr[i-1]<0:arr[i]*=-1
  for iteration in range(4):
   old=arr.copy()
   for f in range(1,22):
    vals=old[np.clip(np.arange(f-2,f+3),0,len(old)-1)];vals=np.where((vals@old[f])[:,None]<0,-vals,vals);v=(vals*kernel[:,None]).sum(0);arr[f]=v/np.linalg.norm(v)
  q[n]=arr
for file in ['hands.blend','texture_ready.blend','uv_master.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work'/file));rig=bpy.data.objects['Rig'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in range(int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(f)
  for n in names:
   pb=rig.pose.bones[n];pb.rotation_quaternion=Quaternion(q[n][f]);pb.keyframe_insert('rotation_quaternion',frame=f)
 a['m488_neck_filtered']=True
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if any(n in fc.data_path for n in names):
      for key in fc.keyframe_points:key.interpolation='LINEAR'
 bpy.ops.wm.save_as_mainfile(filepath=str(p/'work'/file))
for name,args in [('jerk_probe.py',[str(p/'work/hands.blend'),'Death']),('audit_motion.py',[str(p/'work/hands.blend'),'Death']),('check_contacts.py',[str(p/'work/hands.blend'),'Death'])]:
 path=p/'scripts'/name;sys.argv=[str(path),'--',*args];runpy.run_path(str(path),run_name='__main__')
