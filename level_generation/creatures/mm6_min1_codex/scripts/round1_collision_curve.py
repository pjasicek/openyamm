"""Fit one smooth wind-up correction instead of independent frame-by-frame collision offsets."""
import bpy,sys,runpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
ctx=runpy.run_path(str(P/'scripts/round1_contacts.py'),init_globals={'INPUT':'work/round1_carrier_poles.blend','OUTPUT':'work/round1_curve_seed.blend','REPORT':'review/round1/curve_seed.json','ROLES':[]})
F=ctx['F'];r=F.r;sc=F.sc;measure=ctx['measure'];a=bpy.data.actions['Attack'];rows=[F.sample(a,f) for f in range(int(a.frame_range[1])+1)];meta=json.loads((P/'work/round1_grip_frames.json').read_text());HF={s:Matrix(meta['frames'][s]) for s in 'RL'};axerest=r.data.bones['Axe'].matrix_local
def pose(f,par):
 F.apply(rows[f]);t=f/sc.render.fps;u=(t-.60)/.35;w=max(0,1-u*u)**3;A=F.M('Axe')@axerest.inverted();A.translation+=Vector(par[:3])*w;neck=F.M('B_Neck');F.setmat('B_Neck',F.transform(Matrix.Rotation(par[3]*w,3,'X')@Matrix.Rotation(par[4]*w,3,'Z')@neck.to_3x3(),neck.translation));angles=[];lengtherror=0
 for si,s in enumerate('RL'):
  un,fn,hn,la,lb,ru,rf,rb,axis=F.armdata[s];U=F.M(un).translation;oldE=F.M(fn).translation;HR=A.to_3x3()@HF[s];H=A@Vector((0,0,meta['grip_z'][s]))-HR@Vector(F.G[s]['handle_centre_hand_local']);v=H-U;d=v.normalized();lengtherror+=max(0,v.length-(la+lb)*.998)**2;dist=min(v.length,(la+lb)*.998);cc=np.clip((la*la+dist*dist-lb*lb)/(2*la*dist),-1,1);center=U+d*la*cc;pole=oldE-center;pole=(pole-d*pole.dot(d)).normalized();pole=Quaternion(d,par[5+si]*w)@pole;E=center+pole*la*math.sqrt(1-cc*cc);up=(E-U).normalized();fo=(H-E).normalized();bend=(fo-up*fo.dot(up)).normalized();UD=F.basis(up,bend)@rb.transposed();UR=UD@F.restb[un].to_3x3();FR=(UD@rf).rotation_difference(fo).to_matrix()@UD@F.restb[fn].to_3x3();F.setmat(un,F.transform(UR,U));F.setmat(fn,F.transform(FR,E));F.setmat(hn,F.transform(HR,H));rel=(FR.inverted()@HR@(F.restb[fn].to_3x3().inverted()@F.restb[hn].to_3x3()).inverted()).to_quaternion();tw=F.twist(rel,axis);swing=(rel@Quaternion(axis,-tw)).angle;angles.append([math.degrees(tw),math.degrees(swing)])
  r.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.6*tw);ua=(F.restb[un].inverted()@F.restb[fn].translation).normalized();ut=F.twist(r.pose.bones[un].rotation_quaternion,ua);r.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(ua,-.5*ut);F.update()
 F.setmat('Axe',A@axerest);return angles,lengtherror
samples=sorted(set(range(65,226,10))|{120,145,155,170,180,195,210});history=[]
def cost(par):
 total=0;worst=0
 for f in samples:
  angles,error=pose(f,par);m=measure();c=ctx['cost'](m,angles)+1e7*error;total+=c;worst=max(worst,c)
 return total/len(samples)+worst+2*np.dot(par[:3],par[:3])+.001*np.dot(par[3:],par[3:])
par=np.zeros(7);best=cost(par)
for step in [.05,.025,.0125,.006,.003]:
 for repeat in range(3):
  changed=False
  for axis in range(7):
   selected=par.copy()
   for sign in [-1,1]:
    test=par.copy();test[axis]+=sign*step*(1 if axis<3 else 6)
    if np.linalg.norm(test[:3])>.18 or max(abs(test[3:]))>math.radians(50):continue
    value=cost(test)
    if value<best:best=value;selected=test;changed=True
   par=selected
  history.append({'step':step,'repeat':repeat,'cost':best,'parameters':par.tolist()});print('CURVE FIT',history[-1],flush=True)
  if not changed:break
out=[]
for f in range(len(rows)):pose(f,par);out.append(F.snapshot())
# Cast uses the same fitted swing, with a distinct 0.4-second chamber hold.
pause=round(.8*sc.render.fps);hold=round(.4*sc.render.fps);solutions={'Attack':out,'Cast':out[:pause+1]+[out[pause]]*hold+out[pause+1:]}
for role,data in solutions.items():
 bpy.data.actions.remove(bpy.data.actions[role]);a=bpy.data.actions.new(role);a.use_fake_user=True;prev={}
 for f,row in enumerate(data):
  F.apply(row);r.animation_data.action=a
  for n in F.names:
   pb=r.pose.bones[n];q=pb.matrix_basis.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  r.animation_data.action=None
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(data)-1
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/'review/round1/collision_curve.json').write_text(json.dumps(history,indent=2));out='work/round1_collision_curve.blend';bpy.ops.wm.save_as_mainfile(filepath=str(P/out));sys.argv=['g','--',out];runpy.run_path(str(P/'scripts/rig_gates_48.py'));runpy.run_path(str(P/'scripts/round1_precision.py'),init_globals={'INPUT':out});runpy.run_path(str(P/'scripts/round1_acceleration.py'),init_globals={'INPUT':out})
