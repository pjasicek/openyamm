"""Smooth the elbow's angle on its IK circle; keep the carrier and both grip frames exact."""
import bpy,sys,runpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_fit as F
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_lod0.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;F.r=r;F.body=b;F.sc=sc;diagnostic={}
from mathutils import Matrix
meta=json.loads((P/'work/round1_grip_frames.json').read_text());HF={s:Matrix(meta['frames'][s]) for s in 'RL'};axerest=r.data.bones['Axe'].matrix_local
for role in ['Attack','Cast']:
 a=bpy.data.actions[role];rows=[];circle={s:[] for s in 'RL'};previous={};phases={};carrier=[];chests=[];original=[];upper=[]
 for f in range(int(a.frame_range[1])+1):
  rows.append(F.sample(a,f));C=F.M('B_Spine2');chests.append(C);A=F.M('Axe')@axerest.inverted();original.append(A);carrier.append(C.inverted()@A);upper.append({s:F.M(F.armdata[s][0]).translation for s in 'RL'})
 def smooth_vector(values,sigma):
  kernel=np.exp(-.5*(np.arange(-3*sigma,3*sigma+1)/sigma)**2);kernel/=kernel.sum()
  return np.stack([np.convolve(np.pad(values[:,i],(3*sigma,3*sigma),mode='edge'),kernel,mode='valid') for i in range(values.shape[1])],1)
 translations=np.array([m.translation[:] for m in carrier]);rotations=[]
 for f,A in enumerate(carrier):
  q=A.to_quaternion();v=np.zeros(4)
  for j in range(max(0,f-12),min(len(carrier),f+13)):
   qq=carrier[j].to_quaternion();v+=np.array(qq)*(1 if q.dot(qq)>=0 else -1)*math.exp(-.5*((j-f)/4)**2)
  rotations.append(Quaternion(v/np.linalg.norm(v)).to_matrix())
 start=translations.copy()
 for iteration in range(12):
  translations=smooth_vector(translations,4)
  for f in range(len(rows)):
   envelope=min(1,f/24,(len(rows)-1-f)/24);translations[f]=start[f]*(1-envelope)+translations[f]*envelope
   A=chests[f]@F.transform(rotations[f],Vector(translations[f]))
   for repeat in range(12):
    for side in 'RL':
     HR=A.to_3x3()@HF[side];H=A@Vector((0,0,meta['grip_z'][side]))-HR@Vector(F.G[side]['handle_centre_hand_local']);U=upper[f][side];v=H-U;la,lb=F.armdata[side][3:5];reach=math.sqrt(la*la+lb*lb+2*la*lb*math.cos(math.radians(25)))
     if v.length>reach:A.translation-=v.normalized()*(v.length-reach)
   translations[f]=(chests[f].inverted()@A).translation
 targets=[]
 for f,row in enumerate(rows):
  F.apply(row);chest=chests[f].to_3x3();A=chests[f]@F.transform(rotations[f],Vector(translations[f]));targets.append(A)
  for side in 'RL':
   un,fn,hn,la,lb,*_=F.armdata[side];U=F.M(un).translation;E=F.M(fn).translation;HR=A.to_3x3()@HF[side];H=A@Vector((0,0,meta['grip_z'][side]))-HR@Vector(F.G[side]['handle_centre_hand_local']);v=H-U;d=v.normalized();length=v.length;cc=np.clip((la*la+length*length-lb*lb)/(2*la*length),-1,1);center=U+d*la*cc;radius=la*math.sqrt(max(0,1-cc*cc));pole=E-center;pole=(pole-d*pole.dot(d)).normalized();ld=chest.inverted()@d;lp=chest.inverted()@pole
   if side not in previous:base=lp
   else:
    pd,pb=previous[side];base=pd.rotation_difference(ld)@pb;base=(base-ld*base.dot(ld)).normalized()
   previous[side]=(ld.copy(),base.copy());phase=math.atan2(ld.dot(base.cross(lp)),base.dot(lp));circle[side].append((center,radius,chest@base,chest@(ld.cross(base)),phase))
 for s in 'RL':
  phases[s]=np.unwrap([x[4] for x in circle[s]]);sigma=globals().get('SIGMA',8);kernel=np.exp(-.5*(np.arange(-3*sigma,3*sigma+1)/sigma)**2);kernel/=kernel.sum();phases[s]=np.convolve(np.pad(phases[s],(3*sigma,3*sigma),mode='edge'),kernel,mode='valid')
 result=[]
 for f,row in enumerate(rows):
  F.apply(row)
  for s in 'RL':
   un,fn,hn,la,lb,ru,rf,rb,axis=F.armdata[s];U=F.M(un).translation;A=targets[f];HR=A.to_3x3()@HF[s];H=F.transform(HR,A@Vector((0,0,meta['grip_z'][s]))-HR@Vector(F.G[s]['handle_centre_hand_local']));center,radius,x,y,_=circle[s][f];EL=center+radius*(x*math.cos(phases[s][f])+y*math.sin(phases[s][f]));up=(EL-U).normalized();fo=(H.translation-EL).normalized();bend=(fo-up*fo.dot(up)).normalized();UD=F.basis(up,bend)@rb.transposed();UR=UD@F.restb[un].to_3x3();FR=(UD@rf).rotation_difference(fo).to_matrix()@UD@F.restb[fn].to_3x3();F.setmat(un,F.transform(UR,U));F.setmat(fn,F.transform(FR,EL));F.setmat(hn,H)
   rel=(FR.inverted()@H.to_3x3()@(F.restb[fn].to_3x3().inverted()@F.restb[hn].to_3x3()).inverted()).to_quaternion();tw=F.twist(rel,axis);r.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.6*tw);ua=(F.restb[un].inverted()@F.restb[fn].translation).normalized();ut=F.twist(r.pose.bones[un].rotation_quaternion,ua);r.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(ua,-.5*ut);F.update()
  F.setmat('Axe',targets[f]@axerest);result.append(F.snapshot())
 prev={}
 for f,row in enumerate(result):
  F.apply(row);r.animation_data.action=a
  for s in 'RL':
   for n in ['UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist']:
    pb=r.pose.bones[f'B_{s}_{n}'];q=pb.rotation_quaternion.copy()
    if pb.name in prev and q.dot(prev[pb.name])<0:q.negate()
    prev[pb.name]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  pb=r.pose.bones['Axe'];pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  r.animation_data.action=None
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
out='work/round1_carrier_poles.blend';bpy.ops.wm.save_as_mainfile(filepath=str(P/out))
runpy.run_path(str(P/'scripts/round1_acceleration.py'),init_globals={'INPUT':out})
sys.argv=['g','--',out];runpy.run_path(str(P/'scripts/rig_gates_48.py'))
runpy.run_path(str(P/'scripts/round1_precision.py'),init_globals={'INPUT':out})
