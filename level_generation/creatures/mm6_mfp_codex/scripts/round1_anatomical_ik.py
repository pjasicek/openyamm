"""Fit elbow poles to the source hand path, with shared anatomical rotation limits."""
import bpy,sys,json,math,shutil,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
for level in range(4):shutil.copy2(P/f'work/round1/lod{level}.blend',P/f'work/round1/pre_ik_lod{level}.blend')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1/lod0.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;rest={n:np.array(b.matrix_local)for n,b in r.data.bones.items()};cfg=json.loads((P/'gates.json').read_text());roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];names=[f'B_{s}_{n}'for s in 'LR'for n in ['UpperArm','Forearm','Hand','ForearmTwist','UpperArmTwist']]
def unit(v):return v/max(np.linalg.norm(v),1e-10)
def basis(a,h):
 a=unit(a);h=unit(h-a*(a@h));return np.column_stack([a,np.cross(h,a),h])
def matrix(R,p):
 M=Matrix(R).to_4x4();M.translation=Vector(p);return M
setup={}
for s in 'LR':
 U,F,H=[rest[f'B_{s}_{n}']for n in ['UpperArm','Forearm','Hand']];u=unit(F[:3,3]-U[:3,3]);f=unit(H[:3,3]-F[:3,3]);h=U[:3,:3]@np.array(cfg['hands'][s]['elbow_hinge_axis']);kn=np.mean([rest[f'B_{s}_Finger{i}'][:3,3]for i in range(5)],axis=0);setup[s]=(U,F,H,u,f,basis(U[:3,:3].T@u,U[:3,:3].T@h).T,basis(F[:3,:3].T@f,F[:3,:3].T@h).T,H[:3,:3].T@unit(kn-H[:3,3]))
report={}
for role in roles:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];end=float(a.frame_range[1]);times=np.linspace(0,end,round(end*48/30)+1);rows=[];changed=0;maxshift=0;unresolved=0
 for t in times:
  sc.frame_set(int(t),subframe=t%1)
  for s in 'LR':
   un,fn,hn=[f'B_{s}_{n}'for n in ['UpperArm','Forearm','Hand']];U,F,H,u0,f0,invUb,invFb,handAxis=setup[s];Up=np.array(r.pose.bones[un].matrix);Fp=np.array(r.pose.bones[fn].matrix);Hp=np.array(r.pose.bones[hn].matrix);parent=r.pose.bones[un].parent;neutralU=np.array(parent.matrix)[:3,:3]@rest[parent.name][:3,:3].T@U[:3,:3];_,oldRoll=G.swing_twist(neutralU.T@Up[:3,:3],U[:3,:3].T@u0)
   if abs(oldRoll)<=55 and role not in ['Death','Dead','Running']:continue
   S,E,W=Up[:3,3],Fp[:3,3],Hp[:3,3].copy();L1=np.linalg.norm(E-S);L2=np.linalg.norm(W-E);fall=1. if role=='Dead'else float(np.clip((t/30-.5)/.45,0,1)) if role=='Death'else 0.;fall=fall*fall*(3-2*fall);W+=np.array([(.12 if s=='L'else -.12)*fall,-.03*fall,0]);Hp[:3,3]=W;direction=unit(W-S);d=np.linalg.norm(W-S);x=(L1*L1-L2*L2+d*d)/(2*d);radius=math.sqrt(max(0,L1*L1-x*x));center=S+direction*x;pole=unit(E-center);cross=np.cross(direction,pole);options=[]
   for degree in range(-180,181,2):
    theta=math.radians(degree);elbow=center+radius*(pole*math.cos(theta)+cross*math.sin(theta))
    if elbow[2]<.025:continue
    uu=unit(elbow-S);ff=unit(W-elbow);hinge=unit(np.cross(uu,ff));RU=basis(uu,hinge)@invUb;_,upperRoll=G.swing_twist(neutralU.T@RU,U[:3,:3].T@u0)
    if abs(upperRoll)>55:continue
    RF=basis(ff,hinge)@invFb;goalH=Hp.copy()
    if role in ['Death','Dead']:
     goalH[:3,:3]=RF@F[:3,:3].T@H[:3,:3]
    for _ in range(2):
     neutralH=RF@F[:3,:3].T@H[:3,:3];wf,wr=G.swing_twist(neutralH.T@goalH[:3,:3],handAxis);excess=float(wr-np.clip(wr,-38,38));RF=np.array(Quaternion(Vector(ff),math.radians(excess)).to_matrix())@RF
    neutralF=RU@U[:3,:3].T@F[:3,:3];_,fr=G.swing_twist(neutralF.T@RF,F[:3,:3].T@f0);neutralH=RF@F[:3,:3].T@H[:3,:3];wf,wr=G.swing_twist(neutralH.T@goalH[:3,:3],handAxis)
    if abs(fr)>82 or abs(fr+wr*.6)>88 or abs(wr)>42 or wf>66:continue
    score=np.linalg.norm(elbow-E)**2+.0000002*degree*degree;options.append((score,elbow,RU,RF,float(upperRoll),float(wr),goalH))
   if not options:unresolved+=1;continue
   _,elbow,RU,RF,ur,wr,goalH=min(options,key=lambda x:x[0]);maxshift=max(maxshift,float(np.linalg.norm(elbow-E)));changed+=1
   r.pose.bones[un].matrix=matrix(RU,S);bpy.context.view_layer.update();r.pose.bones[fn].matrix=matrix(RF,elbow);bpy.context.view_layer.update();r.pose.bones[hn].matrix=Matrix(goalH);bpy.context.view_layer.update();axisF=F[:3,:3].T@f0;axisU=U[:3,:3].T@u0;r.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(Vector(axisF),math.radians(wr*.6));r.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(Vector(axisU),math.radians(-ur*.5))
  bpy.context.view_layer.update();rows.append({n:r.pose.bones[n].rotation_quaternion.copy()for n in names})
 # Small temporal smoothing removes the discrete pole-search steps.
 if changed:
  raw=rows;rows=[];sigma=.065
  for i,f in enumerate(times):
   dt=(times-f)/30;ix=np.flatnonzero(abs(dt)<sigma*3);weights=np.exp(-.5*(dt[ix]/sigma)**2);row={}
   for n in names:
    ref=raw[i][n];q=sum((np.array(raw[j][n])*(1 if ref.dot(raw[j][n])>=0 else -1)*w for j,w in zip(ix,weights)),np.zeros(4));row[n]=Quaternion(q/np.linalg.norm(q))
   rows.append(row)
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in list(bag.fcurves):
      if any(fc.data_path==f'pose.bones["{n}"].rotation_quaternion'for n in names):bag.fcurves.remove(fc)
  for t,row in zip(times,rows):
   for n,q in row.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=t)
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
 a.use_fake_user=True;report[role]={'adjusted_samples':changed,'no_feasible_pole_samples':unresolved,'maximum_elbow_shift_m':maxshift};print('POLE_FIT',role,report[role],flush=True)
(P/'review/round1/elbow_pole_fit.json').write_text(json.dumps(report,indent=2))
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1/lod0.blend'))
for level in range(1,4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=None
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/round1/lod0.blend'),link=False)as(src,dst):dst.actions=list(roles)
 for a in dst.actions:a.use_fake_user=True
 r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'))
(P/'review/round1/elbow_pole_fit.json').write_text(json.dumps(report,indent=2))
