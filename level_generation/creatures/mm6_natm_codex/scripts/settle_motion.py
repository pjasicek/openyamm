import bpy,math,numpy as np
from pathlib import Path
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/contact_valid_unsmoothed.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;cached={};names=[p.name for p in rig.pose.bones]
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];frames=[];end=int(act.frame_range[1]);target={'Attack':60,'Hit':30}.get(act.name,end)
 for f in range(target+1):
  sf=f*end/target;sc.frame_set(int(sf),subframe=sf-int(sf));frames.append({n:(rig.pose.bones[n].location.copy(),rig.pose.bones[n].rotation_quaternion.copy().normalized())for n in names})
 if act.name=='Death':
  old=frames;frames=[p.copy()for p in old]
  for n in names:
   if not any(n.startswith('B_'+sd+'_')and any(t in n for t in ['UpperArm','Forearm','Hand'])for sd in 'LR'):continue
   for f in range(len(old)):
    centre=old[f][n][1];qv=np.zeros(4);total=0
    for k in range(max(0,f-4),min(len(old),f+5)):
     w=math.exp(-(f-k)**2/(2*1.3**2));q=old[k][n][1];q=-q if q.dot(centre)<0 else q;qv+=np.array(q)*w;total+=w
    frames[f][n]=(old[f][n][0],Quaternion(qv/total).normalized())
 cached[act.name]=frames
cached['Dead']=[cached['Death'][-1]]*2
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for name,frames in cached.items():
 act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data.action=act;prev={}
 for f,pose in enumerate(frames):
  for n,(l,q)in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb=rig.pose.bones[n];pb.location=l;pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.scale=(1,1,1);pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis'or n.startswith('Cloth'):pb.keyframe_insert('location',frame=f)
 act.use_frame_range=True;act.frame_start=0;act.frame_end=len(frames)-1
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/contact_master.blend'))
