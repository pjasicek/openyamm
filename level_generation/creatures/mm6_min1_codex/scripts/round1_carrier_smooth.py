import bpy,sys,runpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_fit as F
bpy.ops.wm.open_mainfile(filepath=str(P/globals().get('INPUT','work/round1_lod0.blend')));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;F.r=r;F.body=b;F.sc=sc;stats={}
for role in ['Attack','Cast']:
 a=bpy.data.actions[role];rows=[];uppers={s:[] for s in 'RL'};axes=[]
 for f in range(int(a.frame_range[1])+1):
  rows.append(F.sample(a,f));axes.append(F.M('Axe'))
  for s in 'RL':uppers[s].append(F.M(f'B_{s}_UpperArm').to_quaternion())
 result=[]
 for f,row in enumerate(rows):
  F.apply(row)
  sigma=12;weights=[math.exp(-.5*((j-f)/sigma)**2) for j in range(max(0,f-36),min(len(rows),f+37))];delta=sum((axes[j].translation*w for j,w in zip(range(max(0,f-36),min(len(rows),f+37)),weights)),Vector())/sum(weights)-axes[f].translation
  for s in 'RL':
   sigma=globals().get('SIGMA',12);qq=uppers[s][f];acc=np.zeros(4);total=0
   for j in range(max(0,f-3*sigma),min(len(rows),f+3*sigma+1)):
    q=uppers[s][j];sign=1 if q.dot(qq)>=0 else -1;w=math.exp(-.5*((j-f)/sigma)**2);acc+=np.array(q)*sign*w;total+=w
   q=Quaternion(acc/np.linalg.norm(acc));un,fn,hn,la,lb,ru,rf,rb,axis=F.armdata[s];U=F.M(un).translation;H=F.M(hn);H.translation+=delta;v=H.translation-U;dd=v.normalized();length=min(v.length,(la+lb)*.999999);cc=max(-1,min(1,(la*la+length*length-lb*lb)/(2*la*length)));direction=q@(F.restb[un].to_3x3().inverted()@ru);pole=(direction-dd*direction.dot(dd)).normalized();EL=U+dd*la*cc+pole*la*math.sqrt(1-cc*cc);up=(EL-U).normalized();fo=(H.translation-EL).normalized();bend=(fo-up*fo.dot(up)).normalized();UD=F.basis(up,bend)@rb.transposed();UR=UD@F.restb[un].to_3x3();FR=(UD@rf).rotation_difference(fo).to_matrix()@UD@F.restb[fn].to_3x3();F.setmat(un,F.transform(UR,U));F.setmat(fn,F.transform(FR,EL));F.setmat(hn,H)
   rel=(FR.inverted()@H.to_3x3()@(F.restb[fn].to_3x3().inverted()@F.restb[hn].to_3x3()).inverted()).to_quaternion();tw=F.twist(rel,axis);r.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.6*tw);ua=(F.restb[un].inverted()@F.restb[fn].translation).normalized();ut=F.twist(r.pose.bones[un].rotation_quaternion,ua);r.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(ua,-.5*ut);F.update()
  ax=axes[f].copy();ax.translation+=delta;F.setmat('Axe',ax);result.append(F.snapshot())
 for f,row in enumerate(result):
  F.apply(row);r.animation_data.action=a
  for s in 'RL':
   for n in ['UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist']:
    pb=r.pose.bones[f'B_{s}_{n}'];pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  r.pose.bones['Axe'].keyframe_insert('rotation_quaternion',frame=f);r.pose.bones['Axe'].keyframe_insert('location',frame=f)
  r.animation_data.action=None

for a in bpy.data.actions:
 for la in a.layers:
  for st in la.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
out=globals().get('OUTPUT','work/round1_carrier_smooth.blend');bpy.ops.wm.save_as_mainfile(filepath=str(P/out))
runpy.run_path(str(P/'scripts/round1_acceleration.py'),init_globals={'INPUT':out})
sys.argv=['g','--',out];runpy.run_path(str(P/'scripts/rig_gates_48.py'))
runpy.run_path(str(P/'scripts/round1_precision.py'),init_globals={'INPUT':out})

