"""Fit the source's hand opening to our fingers; share continuous wrist roll across forearm and wrist."""
from pathlib import Path
import bpy,sys,json,math,numpy as np
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/weighted_hands.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;fj=json.loads((p/'work/finger_joints.json').read_text());fists={s:json.loads((p/f'work/fist_{s}.json').read_text())['finger_local'] for s in 'LR'}
chains={s:{} for s in 'LR'}
for s in 'LR':
 for i in range(5):
  ns=[f'B_{s}_Finger{i}']
  while len(ns)<3:ns.append(next(b.name for b in rig.data.bones if b.parent and b.parent.name==ns[-1]))
  chains[s][i]=ns
reports={}
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];frames=range(int(act.frame_range[1])+1);captured={s:[] for s in 'LR'}
 for f in frames:
  sc.frame_set(f)
  for s in 'LR':
   fa=rig.pose.bones[f'B_{s}_Forearm'];hand=rig.pose.bones[f'B_{s}_Hand'];axis=(fa.bone.matrix_local.inverted()@hand.bone.head_local).normalized()
   rest=(fa.bone.matrix_local.inverted()@hand.bone.matrix_local).to_quaternion();dq=(fa.matrix.inverted()@hand.matrix).to_quaternion()@rest.inverted()
   v=Vector((dq.x,dq.y,dq.z));theta=2*math.atan2(v.dot(axis),dq.w);theta=(theta+math.pi)%(2*math.pi)-math.pi;tw=Quaternion(axis,theta);swing=dq@tw.inverted()
   if swing.w<0:swing=-swing
   closures=[]
   for i in (1,2,3,4):
    ns=chains[s][i];pts=[rig.pose.bones[n].head.copy() for n in ns];tip=rig.pose.bones[ns[-1]].matrix@rig.data.bones[ns[-1]].matrix_local.inverted()@Vector(fj[s][ns[-1]+'_tip']);pts.append(tip)
    extent=(pts[-1]-pts[0]).length/sum((b-a).length for a,b in zip(pts[:-1],pts[1:]));closures.append(np.clip((1-extent)/.55,.10,1))
   captured[s].append((theta,swing.copy(),float(np.mean(closures)),axis.copy(),rest.copy()))
 angles={s:np.unwrap([x[0] for x in captured[s]]) for s in 'LR'}
 for s in 'LR':angles[s]-=round(float(np.median(angles[s]))/(2*math.pi))*2*math.pi
 prev={};rec={s:{'raw_twist_deg':[float(np.min(angles[s])*180/math.pi),float(np.max(angles[s])*180/math.pi)],'closure_range':[min(x[2] for x in captured[s]),max(x[2] for x in captured[s])]} for s in 'LR'}
 for f in frames:
  sc.frame_set(f);rig.animation_data.action=None
  for s in 'LR':
   raw,swing,closure,axis,rest=captured[s][f]
   closure=min(1,closure*1.35)
   if act.name=='Attack':
    a=min(1,f/21,(act.frame_range[1]-f)/6);a=a*a*(3-2*a);closure=max(closure,.249+(1-.249)*a)
   theta=angles[s][f];aa=abs(theta);limit=math.radians(160);span=math.radians(15)
   theta=math.copysign(limit+span*math.tanh((aa-limit)/span),theta) if aa>limit else theta
   if swing.angle>math.radians(58):swing=Quaternion().slerp(swing,math.radians(58)/swing.angle)
   fa=rig.pose.bones[f'B_{s}_Forearm'];hand=rig.pose.bones[f'B_{s}_Hand'];M=(fa.matrix.to_3x3()@(swing@Quaternion(axis,theta)@rest).to_matrix()).to_4x4();M.translation=hand.head.copy();hand.matrix=M;bpy.context.view_layer.update()
   rig.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(axis,theta*.5)
   for n,q in fists[s].items():rig.pose.bones[n].rotation_quaternion=Quaternion().slerp(Quaternion(q),closure)
  baked={n:rig.pose.bones[n].rotation_quaternion.copy() for s in 'LR' for n in [f'B_{s}_Hand',f'B_{s}_ForearmTwist',*fists[s]]}
  rig.animation_data.action=act
  for n,q in baked.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 reports[act.name]=rec;print('HANDS',act.name,rec,flush=True)
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     if any(n in fc.data_path for n in baked):
      for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None
(p/'review/hand_adaptation.json').write_text(json.dumps(reports,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/hands.blend'))
