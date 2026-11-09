import bpy,sys,runpy,json,numpy as np
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];frames=np.arange(0,float(a.frame_range[1])+.001,.25);names=[f'B_{sd}_{b}'for sd in 'LR'for b in ['UpperArm','UpperArmTwist']];qs={n:[]for n in names}
for f in frames:
 sc.frame_set(int(f),subframe=float(f%1))
 for n in names:
  q=r.pose.bones[n].rotation_quaternion.copy()
  if qs[n] and q.dot(Quaternion(qs[n][-1]))<0:q=-q
  qs[n].append(list(q))
for n,values in qs.items():
 arr=np.array(values);sm=[]
 for i,f in enumerate(frames):
  weights=np.exp(-.5*((frames-f)/1.2)**2);weights[abs(frames-f)>3.6]=0;q=(arr*weights[:,None]).sum(0);q/=np.linalg.norm(q);w=min(1,max(0,(f/30-1.03)/.12))*min(1,max(0,(1.52-f/30)/.12));sm.append(Quaternion(arr[i]).slerp(Quaternion(q),w))
 for f,q in zip(frames,sm):r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=float(f))
for layer in a.layers:
 for strip in layer.strips:
  for cb in strip.channelbags:
   for fc in cb.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_smoothed.blend'));runpy.run_path(str(P/'scripts/fix_club_transport.py'),run_name='__main__')
for n in ['elbow_gate.py','audit_motion.py','candidate_prop.py']:
 sys.argv=[n,'--','work/reduction_master.blend','motion_final'];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
runpy.run_path(str(P/'scripts/export_trace.py'),run_name='__main__')
