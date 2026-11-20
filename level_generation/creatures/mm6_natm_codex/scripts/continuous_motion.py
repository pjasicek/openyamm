"""Continuous anatomical poles for library action gestures; keep planted legs and cloth samples."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/authoring_high.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
import arm_ik
sides={s:arm_ik.Side(s)for s in 'LR'};names=[b.name for b in rig.pose.bones]
def smooth_quats(qs,sigma):
 out=[]
 for f,centre in enumerate(qs):
  v=np.zeros(4)
  for k in range(max(0,f-5),min(len(qs),f+6)):
   q=qs[k];v+=np.array(q if q.dot(centre)>=0 else -q)*math.exp(-.5*((k-f)/sigma)**2)
  out.append(Quaternion(v).normalized())
 return out
def smooth_vec(vs,sigma):
 out=[]
 for f in range(len(vs)):
  ids=list(range(max(0,f-5),min(len(vs),f+6)));w=np.exp(-.5*((np.array(ids)-f)/sigma)**2);out.append(Vector(np.average(np.array([vs[k]for k in ids]),axis=0,weights=w)))
 return out
def short(a,b):return math.degrees(2*math.acos(min(1,abs(a.dot(b)))))
for role in ['Attack','Cast','Hit']:
 old=bpy.data.actions[role];rig.animation_data.action=old;rig.animation_data.action_slot=old.slots[0];poses=[];world={s:[]for s in 'LR'}
 for f in range(int(old.frame_range[1])+1):
  sc.frame_set(f);poses.append({n:(rig.pose.bones[n].location.copy(),rig.pose.bones[n].rotation_quaternion.copy())for n in names})
  for sd in 'LR':world[sd].append((rig.pose.bones[f'B_{sd}_Hand'].matrix.copy(),rig.pose.bones[f'B_{sd}_Forearm'].head.copy()))
 smooth={}
 for sd in 'LR':
  smooth[sd]=(smooth_vec([w[0].translation for w in world[sd]],1.3),smooth_quats([w[0].to_quaternion()for w in world[sd]],1.3),smooth_vec([w[1]for w in world[sd]],2.2))
 for n in names:
  if n.startswith(('B_Spine','B_Neck','B_Head'))or'Clavicle'in n:
   qs=smooth_quats([p[n][1]for p in poses],1.3)
   for f,q in enumerate(qs):poses[f][n]=(poses[f][n][0],q)
 rig.animation_data.action=None;previous={};fitted=[]
 for f,pose in enumerate(poses):
  for n,(loc,q)in pose.items():pb=rig.pose.bones[n];pb.location=loc;pb.rotation_quaternion=q
  bpy.context.view_layer.update()
  for sd in 'LR':
   obj=sides[sd];W=smooth[sd][0][f];Rh=smooth[sd][1][f].to_matrix();S=rig.pose.bones[f'B_{sd}_UpperArm'].head.copy();axis=(W-S).normalized();pole=smooth[sd][2][f]-S;pole-=axis*pole.dot(axis)
   if pole.length<.001:pole=Vector((0,1,0))
   pole.normalize();candidates=[]
   parent=rig.pose.bones[f'B_{sd}_Clavicle'].matrix.to_3x3()@obj.rel['Arm']
   for deg in range(-180,180,5):
    r=obj.pose_anatomical(W+Rh@obj.grip_hand,Rh,Quaternion(axis,math.radians(deg))@pole);q=r['Ra'].to_quaternion();upper=arm_ik.swing_twist_deg((parent.inverted()@r['Ra']).to_quaternion(),obj.uA)[1]
    cost=.025*abs(deg)+.10*abs(upper)+.12*abs(r['tw'])+.10*r['sw']+3*max(0,abs(upper)-70)+5*max(0,r['sw']-65)
    if 1.02<r['E'].z<1.43:cost+=max(0,.19-abs(r['E'].x))*1500
    if sd in previous:cost+=3*short(previous[sd],q)
    candidates.append((cost,r))
   r=min(candidates,key=lambda x:x[0])[1];obj.apply(r);previous[sd]=r['Ra'].to_quaternion()
   fb=rig.data.bones[f'B_{sd}_Forearm'];hb=rig.data.bones[f'B_{sd}_Hand'];ub=rig.data.bones[f'B_{sd}_UpperArm'];seg=(fb.matrix_local.inverted()@hb.head_local).normalized()
   rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=arm_ik.swing_twist_deg(rel@rr.inverted(),seg)[1]
   rig.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(seg,math.radians(max(-85,min(85,.65*tw))))
   ax=(ub.matrix_local.inverted()@fb.head_local).normalized();uw=arm_ik.swing_twist_deg(rig.pose.bones[ub.name].rotation_quaternion,ax)[1];rig.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,math.radians(-.5*uw))
  fitted.append({n:(rig.pose.bones[n].location.copy(),rig.pose.bones[n].rotation_quaternion.copy())for n in names})
 bpy.data.actions.remove(old);a=bpy.data.actions.new(role);a.use_fake_user=True;rig.animation_data.action=a;prev={}
 for f,pose in enumerate(fitted):
  for n,(loc,q)in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=loc;pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis'or n.startswith('Cloth'):pb.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(fitted)-1
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 print('CONTINUOUS',role,flush=True)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_continuous.blend'))
