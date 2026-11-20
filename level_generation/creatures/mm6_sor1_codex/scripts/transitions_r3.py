"""Blend free phases in anatomical joint coordinates; fixed grip frames remain untouched."""
import bpy,sys,math,json,runpy
from pathlib import Path
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_radial_approach.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;act=bpy.data.actions['Attack'];stand=bpy.data.actions['Standing']
def attach(a):rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
def smooth(t):t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
def sample(sd,a,f):
 attach(a);scene.frame_set(f);U,F,H=[rig.pose.bones[f'B_{sd}_{n}'] for n in ['UpperArm','Forearm','Hand']];u=(F.head-U.head).normalized();v=(H.head-F.head).normalized();hinge=U.matrix.to_3x3()@cal[sd]['h'];bend=math.atan2(hinge.dot(u.cross(v)),u.dot(v));Rf=U.matrix.to_3x3()@cal[sd]['rel'];Rf=(Rf@cal[sd]['f']).rotation_difference(v).to_matrix()@Rf;q=(F.matrix.to_3x3()@Rf.inverted()).to_quaternion();roll=(2*math.atan2(Vector((q.x,q.y,q.z)).dot(v),q.w)+math.pi)%(2*math.pi)-math.pi
 return {'bend':bend,'roll':roll,'q':{n:rig.pose.bones[f'B_{sd}_{n}'].rotation_quaternion.copy() for n in ['UpperArm','Hand','UpperArmTwist','ForearmTwist']}}
cal={}
for sd in 'LR':
 U,F,H=[rig.data.bones[f'B_{sd}_{n}'] for n in ['UpperArm','Forearm','Hand']];u=(F.head_local-U.head_local).normalized();v=(H.head_local-F.head_local).normalized();h=u.cross(v).normalized();cal[sd]={'h':U.matrix_local.to_3x3().inverted()@h,'rel':U.matrix_local.to_3x3().inverted()@F.matrix_local.to_3x3(),'f':F.matrix_local.to_3x3().inverted()@v,'restbend':u.angle(v)}
ranges=[('L',0,78,sample('L',stand,0),sample('L',act,78)),('L',225,300,sample('L',act,225),sample('L',stand,0)),('R',205,300,sample('R',act,205),sample('R',stand,0))]
for sd,start,end,a,b in ranges:
 for f in range(start,end+1):
  attach(act);scene.frame_set(f);pose={n:pb.matrix_basis.copy() for n,pb in rig.pose.bones.items()};rig.animation_data.action=None
  for n,m in pose.items():rig.pose.bones[n].matrix_basis=m
  w=smooth((f-start)/(end-start));U=rig.pose.bones[f'B_{sd}_UpperArm'];F=rig.pose.bones[f'B_{sd}_Forearm'];H=rig.pose.bones[f'B_{sd}_Hand'];U.rotation_quaternion=a['q']['UpperArm'].slerp(b['q']['UpperArm'],w);bpy.context.view_layer.update();Ra=U.matrix.to_3x3();angle=a['bend']*(1-w)+b['bend']*w;roll=a['roll']*(1-w)+b['roll']*w;Rf=Quaternion(Ra@cal[sd]['h'],angle-cal[sd]['restbend']).to_matrix()@Ra@cal[sd]['rel'];Rf=Quaternion((Rf@cal[sd]['f']).normalized(),roll).to_matrix()@Rf;M=Rf.to_4x4();M.translation=F.head;F.matrix=M;bpy.context.view_layer.update();H.rotation_quaternion=a['q']['Hand'].slerp(b['q']['Hand'],w)
  for n in ['UpperArmTwist','ForearmTwist']:rig.pose.bones[f'B_{sd}_{n}'].rotation_quaternion=a['q'][n].slerp(b['q'][n],w)
  qs={n:rig.pose.bones[f'B_{sd}_{n}'].rotation_quaternion.copy() for n in ['UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist']};attach(act)
  for n,q in qs.items():pb=rig.pose.bones[f'B_{sd}_{n}'];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
runpy.run_path(str(p/'scripts/normalize_keys_r2.py'));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round3_motion.blend'))
