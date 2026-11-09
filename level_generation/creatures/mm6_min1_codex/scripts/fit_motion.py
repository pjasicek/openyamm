"""Mirror the owned axe performance to native right-hand lead; solve both hands and planted steps."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v5.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
names=[b.name for b in rig.data.bones];S=Matrix.Diagonal((-1,1,1));G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'RL'}
SF={n:Matrix(v['rot']) for n,v in json.loads((P/'work/source_rest.json').read_text()).items()}
roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget'];raw={}
def setact(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def update():bpy.context.view_layer.update()
def M(n):return (rig.matrix_world@rig.pose.bones[n].matrix).copy()
def snap():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def apply(p):
 setact(None)
 for n,(q,l) in p.items():rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l;rig.pose.bones[n].scale=(1,1,1)
 update()
def setrot(n,r):
 m=r.to_quaternion().to_matrix().to_4x4();m.translation=M(n).translation;rig.pose.bones[n].matrix=rig.matrix_world.inverted()@m;rig.pose.bones[n].scale=(1,1,1);update()
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def other(n):return n.replace('B_R_','B_L_') if n.startswith('B_R_') else n.replace('B_L_','B_R_') if n.startswith('B_L_') else n
for nm in roles:
 a=bpy.data.actions[nm];setact(a);rows=[]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f)
  for pb in rig.pose.bones:pb.scale=(1,1,1)
  update();rows.append({n:M(n) for n in names})
 raw[nm]=rows
setact(None)
def mirrored(row):
 for n in names:
  if 'Finger' in n or 'Twist' in n:continue
  src=other(n);D=row[src].to_3x3()@SF[src].inverted();r=S@D@S@SF[n]
  m=r.to_4x4();m.translation=S@row[src].translation if n=='B_Pelvis' else M(n).translation
  rig.pose.bones[n].matrix=rig.matrix_world.inverted()@m;rig.pose.bones[n].scale=(1,1,1);update()
 for s in 'RL':
  for n,q in G[s]['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion(q)
 update();return snap()
poses={nm:[mirrored(row) for row in rows] for nm,rows in raw.items()}
meta={}
for nm,pp in poses.items():
 meta[nm]=[]
 for pose in pp:
  apply(pose);meta[nm].append({'chest':M('B_Spine2').to_3x3(),'pelvis':M('B_Pelvis').translation.copy()})
apply(poses['Standing'][0]);line=M('B_L_UpperArm').translation-M('B_R_UpperArm').translation;stance_yaw=math.atan2(line.y,line.x);CAL=Matrix.Rotation(-stance_yaw,3,'Z')
for nm,pp in poses.items():
 for i,pose in enumerate(pp):
  cal=Matrix.Rotation(-stance_yaw*(1-smooth(i/20)),3,'Z') if nm=='Death' else CAL
  apply(pose);headR=M('B_Head').to_3x3();setrot('B_Spine',cal@M('B_Spine').to_3x3());setrot('B_Head',headR);pp[i]=snap()
standing=poses['Standing'][0];apply(standing)
HOME={s:M(f'B_{s}_Foot') for s in 'LR'};CHEST0=M('B_Spine2').to_3x3();PEL=M('B_Pelvis').translation.copy()
# Native handle direction rises towards the minotaur's right hand; the source is left-handed and nearly horizontal.
rawL=raw['Standing'][0]['B_L_Hand'];oldaxis=S@(rawL.to_3x3()@Vector(G['L']['handle_axis_hand_local']))
wantaxis=Vector((-.85,-.30,.43)).normalized();axislocal=rawL.to_3x3().inverted()@S@CAL.inverted()@wantaxis
STC=M('B_Pelvis').translation+CAL@(S@(rawL@Vector(G['L']['handle_centre_hand_local']))-S@raw['Standing'][0]['B_Pelvis'].translation)+Vector((0,-.10,.28))
legs=[n for n in names if any(x in n for x in ['Thigh','Calf','Foot','Toe'])]
RESTPEL=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
def aim(n,child,d):
 m=M(n);cur=M(child).translation-m.translation;r=cur.normalized().rotation_difference(d.normalized()).to_matrix();t=m.translation.copy();m=r.to_4x4()@m;m.translation=t;rig.pose.bones[n].matrix=rig.matrix_world.inverted()@m;rig.pose.bones[n].scale=(1,1,1);update()
def ik(s,parts,target,rot,pole=None):
 a,b,c=[f'B_{s}_{x}' for x in parts];h,k,e=[M(x).translation for x in [a,b,c]];la=(k-h).length;lb=(e-k).length;v=target-h;d=min(v.length,(la+lb)*.999);u=v.normalized()
 pol=(k-h) if pole is None else pole;pol=pol-u*pol.dot(u)
 if pol.length<1e-5:pol=Vector((0,-1,0))-u*u.y*-1
 pol.normalize();co=max(-1,min(1,(la*la+d*d-lb*lb)/(2*la*d)));kn=h+la*(u*co+pol*math.sqrt(max(0,1-co*co)))
 aim(a,b,kn-h);aim(b,c,target-M(b).translation);setrot(c,rot)
 return (M(c).translation-target).length
plans={}
for nm in ['Attack','Cast','Fidget']:
 pp=poses[nm];worldsp=[];ank={s:[] for s in 'LR'}
 for pose in pp:
  apply(pose);worldsp.append(M('B_Spine').to_3x3())
  for n in ['B_Pelvis']+legs:
   q,l=pose[n];q0,l0=standing[n];pose[n]=(q0.slerp(q if q.dot(q0)>=0 else -q,.2),l0.lerp(l,.2))
  apply(pose);setrot('B_Spine',worldsp[-1]);pose['B_Spine']=snap()['B_Spine']
  for s in 'LR':ank[s].append(M(f'B_{s}_Foot').translation.copy())
 nf=len(pp);plan={}
 for s in 'LR':
  home=HOME[s].translation;off=[(v-home).length for v in ank[s]];km=int(np.argmax(off));delta=ank[s][km]-home;delta.z=0
  if delta.length>.15:delta*=.15/delta.length
  if delta.length>.025:plan[s]={'start':max(4,min(km-3,nf//3)),'delta':list(delta)}
 order=sorted(plan,key=lambda s:plan[s]['start'])
 for j,s in enumerate(order):
  if j:plan[s]['start']=max(plan[s]['start'],plan[order[j-1]]['start']+6)
  plan[s]['back_end']=nf-1-j*6
 for f,pose in enumerate(pp):
  apply(pose)
  for s in 'LR':
   t=HOME[s].translation.copy()
   if s in plan:
    pl=plan[s];a=pl['start'];b=pl['back_end'];d=Vector(pl['delta'])
    if a<f<a+6:u=(f-a)/6;t+=d*smooth(u);t.z+=.035*math.sin(math.pi*u)
    elif a+6<=f<=b-6:t+=d
    elif b-6<f<b:u=(f-b+6)/6;t+=d*(1-smooth(u));t.z+=.035*math.sin(math.pi*u)
   toe=HOME[s].to_3x3()@(rig.data.bones[f'B_{s}_Foot'].matrix_local.inverted()@rig.data.bones[f'B_{s}_Toe0'].head_local);toe.z=0
   ik(s,('Thigh','Calf','Foot'),t,HOME[s].to_3x3(),toe)
  pp[f]=snap()
 plans[nm]=plan
# Soft bound trunk axial twist, retaining source head direction.
sp=['B_Spine','B_Spine1','B_Spine2'];axes={n:(rig.data.bones[n].matrix_local.inverted()@rig.data.bones[c].head_local).normalized() for n,c in zip(sp,['B_Spine1','B_Spine2','B_Neck'])}
def twist(q,ax):return (2*math.atan2(Vector(q[1:]).dot(ax),q.w)+math.pi)%(2*math.pi)-math.pi
for nm in ['Attack','Cast','Fidget']:
 for pose in poses[nm]:
  apply(pose);headworld=M('B_Head').to_3x3()
  ts={n:twist(pose[n][0],axes[n]) for n in sp};total=sum(ts.values());limit=math.radians(42)*math.tanh(total/math.radians(42));k=limit/total if abs(total)>1e-7 else 1
  for n in sp:
   q,l=pose[n];pose[n]=(q@Quaternion(axes[n],-ts[n])@Quaternion(axes[n],ts[n]*k),l)
  apply(pose);setrot('B_Head',headworld);pose['B_Head']=snap()['B_Head']
for nm,keep in [('Death',.15),('Fidget',.5)]:
 for pose in poses[nm]:
  for n in ['B_Neck','B_Head']:
   q,l=pose[n];q0=standing[n][0];pose[n]=(q0.slerp(q if q.dot(q0)>=0 else -q,keep),l)
for nm in ['Fidget','Hit']:
 for pose in poses[nm]:
  for n in names:
   if n=='B_Pelvis' or (nm=='Fidget' and n in ['B_Head','B_Neck']) or any(x in n for x in ['Thigh','Calf','Foot','Toe','Finger']):continue
   q,l=pose[n];q0,l0=standing[n];pose[n]=(q0.slerp(q if q.dot(q0)>=0 else -q,.15 if nm=='Fidget' else .4),l0.lerp(l,.15 if nm=='Fidget' else .4))
# The bull's wide shoulders need a native chamber rather than the human clip's crossed-arm recovery.
apply(standing);standSpine=M('B_Spine').to_3x3();standHead=M('B_Head').to_3x3()
def beat(f,keys):
 for (a,va),(b,vb) in zip(keys,keys[1:]):
  if f<=b:return va+(vb-va)*smooth((f-a)/(b-a))
 return keys[-1][1]
for nm in ['Attack','Cast']:
 for f,pose in enumerate(poses[nm]):
  for n in names:
   if n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'] or any(k in n for k in ['Clavicle','UpperArm','Forearm','Hand']):pose[n]=standing[n]
  apply(pose);yaw=math.radians(beat(f,[(0,0),(10,-12),(18,12),(27,0),(50,0)]));lean=math.radians(beat(f,[(0,0),(12,-3),(20,6),(32,2),(50,0)]))
  setrot('B_Spine',Matrix.Rotation(yaw,3,'Z')@Matrix.Rotation(lean,3,'X')@standSpine);setrot('B_Head',Matrix.Rotation(yaw*.2,3,'Z')@standHead);poses[nm][f]=snap()
for f,pose in enumerate(poses['Death']):
 # Ease into the fall from the held stance, retaining the source root collapse.
 u=smooth(f/10)
 for n in names:
  q,l=pose[n];q0,l0=standing[n];pose[n]=(q0.slerp(q if q.dot(q0)>=0 else -q,u*(.6 if n in legs else 1)),l0.lerp(l,u))
 poses['Death'][f]=pose
def griprotation(s,A,forward):
 localA=Vector(G[s]['handle_axis_hand_local']);localY=Vector(G[s]['handle_centre_hand_local']);localY=(localY-localA*localY.dot(localA)).normalized()
 y=(forward-A*forward.dot(A)).normalized();world=Matrix((A,y,A.cross(y))).transposed();local=Matrix((localA,localY,localA.cross(localY))).transposed()
 return world@local.transposed()
# Native axe beats. Cubic tangents keep the actual cutting stroke moving through the target beat.
attack_keys=[(0,list(STC),list(wantaxis)),(8,[-.35,-.40,1.36],[-.5,-.15,.85]),(13,[-.35,-.42,1.46],[-.5,-.12,.85]),(18,[-.13,-.62,1.25],[-.65,-.60,.25]),(24,[-.10,-.52,1.10],[-.70,-.65,-.20]),(33,[.02,-.50,1.13],[-.60,-.70,.20]),(50,list(STC),list(wantaxis))]
def native_path(f):
 i=next((i for i in range(len(attack_keys)-1) if f<=attack_keys[i+1][0]),len(attack_keys)-2);k0,k1=attack_keys[i:i+2];dt=k1[0]-k0[0];u=(f-k0[0])/dt;out=[]
 for col in [1,2]:
  a=Vector(k0[col]);b=Vector(k1[col]);prev=attack_keys[max(0,i-1)];nxt=attack_keys[min(len(attack_keys)-1,i+2)];m0=(b-Vector(prev[col]))/(k1[0]-prev[0]);m1=(Vector(nxt[col])-a)/(nxt[0]-k0[0]);out.append((2*u**3-3*u*u+1)*a+(u**3-2*u*u+u)*dt*m0+(-2*u**3+3*u*u)*b+(u**3-u*u)*dt*m1)
 return out[0],out[1].normalized()
# Both wrist targets come from one rigid shaft, with no stretched or translated limb bones.
GRIP_Z=.70;SPACING=.45;fits={};out={};axe_mats={}
for nm,pp in poses.items():
 rr=[];am=[];maxerr=0;maxshift=0
 for f,pose in enumerate(pp):
  apply(pose)
  SPACING=.45-(.07*smooth((f-5)/8)*smooth((43-f)/10) if nm in ['Attack','Cast'] else 0)
  src=raw[nm][f]['B_L_Hand'];C=S@(src@Vector(G['L']['handle_centre_hand_local']));A=(S@src.to_3x3()@axislocal).normalized()
  # Carry the native-height correction in the current chest frame, independently from pelvis planting.
  D=M('B_Spine2').to_3x3()@meta[nm][f]['chest'].inverted();rawpel=S@raw[nm][f]['B_Pelvis'].translation;C=M('B_Pelvis').translation+D@(C-rawpel);A=(D@A).normalized()
  C+=M('B_Spine2').to_3x3()@CHEST0.inverted()@Vector((0,-.10,.28))*(max(0,1-f/8) if nm=='Death' else 1)
  if nm=='Fidget':
   C=STC+(C-STC)*.25
   A=wantaxis.lerp(A,.25).normalized()
  if nm in ['Attack','Cast']:
   C,A=native_path(f);C+=M('B_Pelvis').translation-PEL;C.y-=max(0,C.y-(-.45+A.y*SPACING))*smooth(f/5)*smooth((50-f)/5)
   lift=math.radians(-9)*smooth((f-4)/5)*smooth((28-f)/8);setrot('B_Neck',Matrix.Rotation(lift,3,'X')@M('B_Neck').to_3x3())
  if nm in ['Hit','Fidget'] or (nm=='Death' and f<6):
   D0=M('B_Spine2').to_3x3()@CHEST0.inverted();C=STC+M('B_Pelvis').translation-PEL;A=wantaxis.copy()
   if nm=='Hit':C.y-=.025
   if nm=='Death':C.y-=.085*smooth(f/5)
  # Fit wrist direction to the forearm around the shared cylindrical grip.
  rotations={}
  for s in 'RL':
   hC=C-(A*SPACING if s=='L' else Vector());rotations[s]=griprotation(s,A,hC-M(f'B_{s}_Forearm').translation)
  helds='RL' if nm!='Death' or f<6 else ''
  offsets={s:rotations[s]@Vector(G[s]['handle_centre_hand_local']) for s in 'RL'}
  initial=C.copy()
  for _ in range(12):
   moved=Vector()
   for s in helds:
    target=C-(A*SPACING if s=='L' else Vector())-offsets[s];sh=M(f'B_{s}_UpperArm').translation;el=M(f'B_{s}_Forearm').translation;wr=M(f'B_{s}_Hand').translation;length=(el-sh).length+(wr-el).length;dv=target-sh
    if dv.length>length*.97:moved-=(dv-dv.normalized()*length*.97)
   C+=moved*.65
   if moved.length<1e-5:break
  maxshift=max(maxshift,(C-initial).length)
  for _ in range(3):
   for s in helds:
    hC=C-(A*SPACING if s=='L' else Vector());rotations[s]=griprotation(s,A,hC-M(f'B_{s}_Forearm').translation);offsets[s]=rotations[s]@Vector(G[s]['handle_centre_hand_local']);target=hC-offsets[s]
    outdir=M('B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((1 if s=='L' else -1,.1,-.2));err=ik(s,('UpperArm','Forearm','Hand'),target,rotations[s],(M(f'B_{s}_Forearm').translation-M(f'B_{s}_UpperArm').translation)+outdir*.035+(M('B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,0,-.16)))*smooth((f-17)/5)*smooth((42-f)/6)*(1 if s=='L' and nm in ['Attack','Cast'] else 0));maxerr=max(maxerr,err)
  if nm=='Death' and f>=6:
   u=smooth((f-9)/14)
   for n in names:
    if any(k in n for k in ['Clavicle','UpperArm','Forearm','Hand']):
     q0=rr[5][n][0];rig.pose.bones[n].rotation_quaternion=q0.slerp(Quaternion(),u)
   update()
   ch=M('B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
   for sd in 'RL':
    n=f'B_{sd}_UpperArm';setrot(n,Matrix.Rotation(math.radians(28)*(1 if sd=='L' else -1)*smooth((f-5)/6),3,ch@Vector((0,-1,0)))@M(n).to_3x3())
  # Re-bake twist helpers after IK using measured child-joint directions.
  for s in 'RL':
   fb=rig.data.bones[f'B_{s}_Forearm'];hb=rig.data.bones[f'B_{s}_Hand'];ax=(fb.matrix_local.inverted()@hb.head_local).normalized();dq=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion()@(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion().inverted()
   rig.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(ax,.5*twist(dq,ax))
   ub=rig.data.bones[f'B_{s}_UpperArm'];uax=(ub.matrix_local.inverted()@fb.head_local).normalized();rig.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(uax,-.5*twist(rig.pose.bones[ub.name].rotation_quaternion,uax))
  update()
  # Ground from the physical skin; cloth does not lift a standing actor.
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear();rest=np.array([tuple(v.co) for v in body.data.vertices]);ids=np.where(rest[:,2]<.13)[0] if nm!='Death' else np.where(np.array([a.value for a in body.data.attributes['piece'].data])==0)[0]
  dz=-float(co[ids,2].min());rig.pose.bones['B_Pelvis'].location+=RESTPEL@Vector((0,0,dz));C.z+=dz;update()
  # Blade face follows source wrist roll; later signed edge gate chooses its fixed axial roll.
  x=rotations['R']@Vector((0,1,0));x=(x-A*x.dot(A)).normalized();y=A.cross(x).normalized();r=Matrix((x,y,A)).transposed();mat=r.to_4x4();mat.translation=C-A*GRIP_Z
  if nm=='Death' and f>=6:
   start=am[5];u=smooth((f-5)/20);side=smooth((f-8)/7);down=smooth((f-11)/14);rot=Vector((0,0,1)).rotation_difference(Vector((0,1,0))).to_matrix();end=rot.to_4x4();end.translation=Vector((-1.15,-.8,.025))
   q=start.to_quaternion().slerp(end.to_quaternion(),down);mat=q.to_matrix().to_4x4();mat.translation=start.translation.lerp(end.translation,down);mat.translation.x=start.translation.x+(-1.15-start.translation.x)*side;mat.translation.y-=.35*smooth((f-5)/4)*(1-down)
   for s in 'RL':
    for n,q0 in G[s]['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion(q0).slerp(Quaternion(),u*.6)
   update()
  am.append(mat);rr.append(snap())
 fits[nm]={'max_wrist_target_error_m':maxerr,'max_carrier_reach_correction_m':maxshift};out[nm]=rr;axe_mats[nm]=am
# The native family has a heavy walk; use its fitted gait as a quicker trot instead of the set's deep sprint.
base=out['Walking'];mats=axe_mats['Walking'];rr=[];am=[]
for f in range(19):
 t=f*(len(base)-1)/18;i=min(int(t),len(base)-2);u=t-i;rr.append({n:(base[i][n][0].slerp(base[i+1][n][0],u),base[i][n][1].lerp(base[i+1][n][1],u)) for n in names});m=mats[i].to_quaternion().slerp(mats[i+1].to_quaternion(),u).to_matrix().to_4x4();m.translation=mats[i].translation.lerp(mats[i+1].translation,u);am.append(m)
out['Running']=rr;axe_mats['Running']=am;fits['Running']={'source':'Walking retimed from 0.8 s to 0.6 s','max_wrist_target_error_m':fits['Walking']['max_wrist_target_error_m']}
# Add a rigid attachment joint whose animation is baked in armature space, so an orchestrator can split it.
apply(standing);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');eb=rig.data.edit_bones.new('Axe');eb.head=(0,0,0);eb.tail=(0,0,.2);eb.parent=rig.data.edit_bones['B_R_Hand'];bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(P/'work/axe.blend'),link=False) as (src,dst):dst.objects=['Axe']
axe=dst.objects[0];bpy.context.collection.objects.link(axe);axe.name='AxeMesh';g=axe.vertex_groups.new(name='Axe');g.add(list(range(len(axe.data.vertices))),1,'REPLACE');mod=axe.modifiers.new('Axe rigid joint','ARMATURE');mod.object=rig
for nm,pp in out.items():
 bpy.data.actions.remove(bpy.data.actions[nm]);act=bpy.data.actions.new(nm);act.use_fake_user=True;prev={}
 for f,pose in enumerate(pp):
  apply(pose);m=axe_mats[nm][f]@rig.data.bones['Axe'].matrix_local;rig.pose.bones['Axe'].matrix=rig.matrix_world.inverted()@m;rig.pose.bones['Axe'].scale=(1,1,1);update();setact(act)
  for n in names+['Axe']:
   pb=rig.pose.bones[n];q=pb.rotation_quaternion.copy()
   if n in prev and q.dot(prev[n])<0:q=-q
   pb.rotation_quaternion=q;pb.scale=(1,1,1);prev[n]=q;pb.keyframe_insert('rotation_quaternion',frame=f)
   if n in ['B_Pelvis','Axe']:pb.keyframe_insert('location',frame=f)
  setact(None)
 act.use_frame_range=True;act.frame_start=0;act.frame_end=len(pp)-1
(P/'work/motion_fit.json').write_text(json.dumps({'handedness':'Mirrored source; right hand leads','shaft_grip_z':GRIP_Z,'hand_spacing_m':SPACING,'leg_motion_keep':.2,'step_plans':plans,'fits':fits},indent=2))
setact(bpy.data.actions['Standing']);sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v6.blend'));common.workbench_clay(sc)
for nm in roles:
 setact(bpy.data.actions[nm]);nf=len(out[nm])
 for i in range(5):
  sc.frame_set(round((nf-1)*i/4));common.render_views(str(P/f'review/fitted_{nm}_{i}'),1,3.2,views=['front','left','three_quarter'],resolution=(280,400))
print('FITTED',json.dumps(fits))
