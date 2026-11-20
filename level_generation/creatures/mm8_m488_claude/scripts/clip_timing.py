"""Blend one-shots with Standing while retaining the selected source clips at 30 fps."""
from pathlib import Path
import sys,bpy,json,numpy as np
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
names=[b.name for b in rig.data.bones]
def take(action,frame):
 rig.animation_data.action=action
 if action.slots:rig.animation_data.action_slot=action.slots[0]
 scene.frame_set(int(frame),subframe=float(frame%1))
 return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def mix(a,b,t):
 t=t*t*(3-2*t)
 return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t)) for n in names}
def bake(name,poses):
 if name in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[name])
 act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data.action=act;prev={}
 for f,pose in enumerate(poses):
  for n,(q,loc) in pose.items():
   q=q.copy()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.location=loc;pb.keyframe_insert('location',frame=f)
 act.use_frame_range=True;act.frame_start=0;act.frame_end=len(poses)-1
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 return act
standing=take(bpy.data.actions['Standing'],0);report={}
for name in ('Standing','Walking','Running','Attack','Hit','Fidget','Death'):
 act=bpy.data.actions[name];poses=[take(act,f) for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1)]
 source_frames=len(poses)
 if name in ('Standing','Walking','Running'):
  delta=poses[-1]['B_Pelvis'][1]-poses[0]['B_Pelvis'][1]
  for i,pose in enumerate(poses):pose['B_Pelvis']=(pose['B_Pelvis'][0],pose['B_Pelvis'][1]-delta*(i/(len(poses)-1)))
  poses[-1]=poses[0]
 elif name=='Attack':
  pre=21;post=6
  poses=[mix(standing,poses[0],i/pre) for i in range(pre)]+poses+[mix(poses[-1],standing,(i+1)/post) for i in range(post)]
  report['attack_impact_seconds']=(21+json.loads((Path(__file__).resolve().parents[1]/'review/punch_aim.json').read_text())['source_extension_frame'])/30
 elif name=='Hit':
  original=poses[:]
  for i in range(4):poses[i]=mix(standing,original[i],i/3)
  for i in range(len(poses)-5,len(poses)):poses[i]=mix(original[i],standing,(i-(len(poses)-5))/4)
 else:
  pre=6;post=6 if name=='Fidget' else 0
  poses=[mix(standing,poses[0],i/pre) for i in range(pre)]+poses+([mix(poses[-1],standing,(i+1)/post) for i in range(post)] if post else [])
 bake(name,poses);report[name]={'source_frames':source_frames,'final_frames':len(poses),'seconds':(len(poses)-1)/30}
 if name=='Death':dead=poses[-1]
bake('Dead',[dead]*31);report['Dead']={'seconds':1,'held':'Death final pose'}
assert report['Hit']['seconds']<=.625 and .8<=report['attack_impact_seconds']<=1.2
rig.animation_data.action=None;scene.render.fps=30;bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
(Path(__file__).resolve().parents[1]/'review/clip_timing.json').write_text(json.dumps(report,indent=2)+'\n');print('CLIP_TIMING',report)
