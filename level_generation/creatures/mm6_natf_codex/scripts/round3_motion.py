"""Only Running and Attack: smooth library gait and a forward cross-body cutting path."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round3/before/work/accepted_master.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=60;names=list(rig.pose.bones.keys())
def attach(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snap():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names}
def sample(a,f):
 attach(a);sc.frame_set(int(f),subframe=f%1);return snap()
def apply(p):
 attach(None)
 for n,(q,l)in p.items():b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l
 bpy.context.view_layer.update()
def mix(a,b,u):return {n:(a[n][0].slerp(b[n][0],u),a[n][1].lerp(b[n][1],u))for n in names}
def interp(a,f):
 f=max(0,min(len(a)-1,f));i=int(f);return mix(a[i],a[min(i+1,len(a)-1)],f-i)
def smooth(t):t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
def world(n):return rig.pose.bones[n].matrix.copy()
def put(n,R):
 m=R.to_4x4();m.translation=world(n).translation;rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
def rotate(n,axis,d):put(n,Matrix.Rotation(math.radians(d),3,axis)@world(n).to_3x3())
def aim(n,child,T):
 m=world(n);put(n,(world(child).translation-m.translation).rotation_difference(T-m.translation).to_matrix()@m.to_3x3())
def leg(sd,T,R):
 th,ca,ft=[f'B_{sd}_{k}'for k in ['Thigh','Calf','Foot']];H=world(th).translation;K=world(ca).translation;A=world(ft).translation;a=(K-H).length;b=(A-K).length;D=T-H;d=min(D.length,(a+b)*.997);u=D.normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);N=H+a*(u*c+v*math.sqrt(max(0,1-c*c)));aim(th,ca,N);aim(ca,ft,T);put(ft,R)
old={r:[sample(bpy.data.actions[r],f)for f in range(int(bpy.data.actions[r].frame_range[1])+1)]for r in ['Standing','Attack']}
with bpy.data.libraries.load(str(P/'work/round3_sources.blend'))as(s,d):d.actions=['RunNormal']
a=bpy.data.actions['RunNormal'];src=[sample(a,f)for f in range(int(a.frame_range[1])+1)];bpy.data.actions.remove(a)
ST=old['Standing'][0];apply(ST);HOME={s:world(f'B_{s}_Foot')for s in 'LR'};PEL=world('B_Pelvis');allposes={};targets={}
for role in ['Running','Attack']:
 poses=[];targetrows=[];duration=.8 if role=='Running'else 2.15
 for fi in range(round(duration*60)+1):
  t=fi/60;u=t/duration
  if role=='Running':
   p=interp(src,u*(len(src)-1))
   # Close the library loop and remove single-sample root-height corrections.
   endblend=smooth((u-.82)/.18);p=mix(p,src[0],endblend)
   for n in names:
    if 'Finger'in n or n in ['ForearmBlade','LeafShield','BladeTip','HemOpening'] or 'Twist'in n or n.startswith('Skirt_'):p[n]=ST[n]
   apply(p);m=PEL.copy();m.translation.z=.835+.008*math.cos(4*math.pi*u);rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
   # Retargeted normal-run torso sway remains, with a smooth upright height curve.
   for n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
    b=rig.pose.bones[n];b.rotation_quaternion=ST[n][0].slerp(p[n][0],.45)
   bpy.context.view_layer.update()
   for sd in 'LR':
    phase=2*math.pi*u+(0 if sd=='L'else math.pi);T=HOME[sd].translation.copy();T.y=HOME[sd].translation.y+.299829*math.cos(phase);T.z+=.13*max(0,math.sin(phase))**2;leg(sd,T,HOME[sd].to_3x3())
   # Fitted hands keep their local grip, with the source run's shoulder swing.
   for sd in 'LR':
    rig.pose.bones[f'B_{sd}_Hand'].rotation_quaternion=ST[f'B_{sd}_Hand'][0]
   bpy.context.view_layer.update()
  else:
   p=interp(old['Attack'],fi);apply(p)
   drive=smooth((t-.53)/.48)*(1-smooth((t-1.25)/.65))
   rotate('B_Spine','Z',28*drive);rotate('B_Spine','X',9*drive);rotate('B_Spine','Y',7*drive)
   # Face stays on the victim while the torso turns through the diagonal.
   rotate('B_Neck','Z',-20*drive);rotate('B_Head','Z',-8*drive);rotate('B_Head','X',-3*drive)
   rotate('B_L_UpperArm','Z',-18*drive);rotate('B_L_UpperArm','X',-10*drive)
   W=world('B_R_Hand').translation;E=world('B_R_Forearm').translation
   target=Vector((.19,-.49,.96));W=W.lerp(target,drive)
   aim('B_R_UpperArm','B_R_Forearm',E+Vector((.04*drive,-.12*drive,0)))
   # The anatomical solve consumes this desired endpoint before fitting the blade roll.
   M=world('B_R_Hand');M.translation=W;targetrows.append({'frame':fi,'wrist':list(W),'drive':drive})
  poses.append(snap())
 allposes[role]=poses
 if role=='Attack':targets[role]=targetrows
for role,poses in allposes.items():
 a=bpy.data.actions[role];bpy.data.actions.remove(a);a=bpy.data.actions.new(role);a.use_fake_user=True;attach(a);prev={}
 for f,p in enumerate(poses):
  for n,(q,l)in p.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.keyframe_insert('rotation_quaternion',frame=f)
   if n in ['B_Pelvis','HemOpening','LeafShield']:b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
 for lay in a.layers:
  for strip in lay.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
attach(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3_motion.blend'))
(P/'review/round3/attack_targets.json').write_text(json.dumps(targets,indent=2))
