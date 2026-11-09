"""Smooth the elbow's angle on its IK circle; keep the carrier and both grip frames exact."""
import bpy,sys,runpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_fit as F
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_lod0.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;F.r=r;F.body=b;F.sc=sc;diagnostic={}
for role in ['Attack','Cast']:
 a=bpy.data.actions[role];rows=[];circle={s:[] for s in 'RL'};previous={};phases={}
 for f in range(int(a.frame_range[1])+1):
  rows.append(F.sample(a,f));chest=F.M('B_Spine2').to_3x3()
  for s in 'RL':
   un,fn,hn,la,lb,*_=F.armdata[s];U=F.M(un).translation;E=F.M(fn).translation;H=F.M(hn).translation;v=H-U;d=v.normalized();length=v.length;cc=np.clip((la*la+length*length-lb*lb)/(2*la*length),-1,1);center=U+d*la*cc;radius=la*math.sqrt(max(0,1-cc*cc));pole=(E-center).normalized();ld=chest.inverted()@d;lp=chest.inverted()@pole
   if s not in previous:base=lp
   else:
    pd,pb=previous[s];base=pd.rotation_difference(ld)@pb;base=(base-ld*base.dot(ld)).normalized()
   previous[s]=(ld.copy(),base.copy());phase=math.atan2(ld.dot(base.cross(lp)),base.dot(lp));circle[s].append((center,radius,chest@base,chest@(ld.cross(base)),phase))
 for s in 'RL':
  phases[s]=np.unwrap([x[4] for x in circle[s]]);sigma=globals().get('SIGMA',8);kernel=np.exp(-.5*(np.arange(-3*sigma,3*sigma+1)/sigma)**2);kernel/=kernel.sum();phases[s]=np.convolve(np.pad(phases[s],(3*sigma,3*sigma),mode='edge'),kernel,mode='valid')
 result=[]
 for f,row in enumerate(rows):
  F.apply(row)
  for s in 'RL':
   un,fn,hn,la,lb,ru,rf,rb,axis=F.armdata[s];U=F.M(un).translation;H=F.M(hn);center,radius,x,y,_=circle[s][f];EL=center+radius*(x*math.cos(phases[s][f])+y*math.sin(phases[s][f]));up=(EL-U).normalized();fo=(H.translation-EL).normalized();bend=(fo-up*fo.dot(up)).normalized();UD=F.basis(up,bend)@rb.transposed();UR=UD@F.restb[un].to_3x3();FR=(UD@rf).rotation_difference(fo).to_matrix()@UD@F.restb[fn].to_3x3();F.setmat(un,F.transform(UR,U));F.setmat(fn,F.transform(FR,EL));F.setmat(hn,H)
   rel=(FR.inverted()@H.to_3x3()@(F.restb[fn].to_3x3().inverted()@F.restb[hn].to_3x3()).inverted()).to_quaternion();tw=F.twist(rel,axis);r.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.6*tw);ua=(F.restb[un].inverted()@F.restb[fn].translation).normalized();ut=F.twist(r.pose.bones[un].rotation_quaternion,ua);r.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(ua,-.5*ut);F.update()
  result.append(F.snapshot())
 prev={}
 for f,row in enumerate(result):
  F.apply(row);r.animation_data.action=a
  for s in 'RL':
   for n in ['UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist']:
    pb=r.pose.bones[f'B_{s}_{n}'];q=pb.rotation_quaternion.copy()
    if pb.name in prev and q.dot(prev[pb.name])<0:q.negate()
    prev[pb.name]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  r.animation_data.action=None
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
out='work/round1_pole_smooth.blend';bpy.ops.wm.save_as_mainfile(filepath=str(P/out))
runpy.run_path(str(P/'scripts/round1_acceleration.py'),init_globals={'INPUT':out})
sys.argv=['g','--',out];runpy.run_path(str(P/'scripts/rig_gates_48.py'))
runpy.run_path(str(P/'scripts/round1_precision.py'),init_globals={'INPUT':out})
