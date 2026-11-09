"""Round 4 native rest, library shot/hit fitting and anatomical wrist roll distribution."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True;import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/sources_complete.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
def action(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def get():return {b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy())for b in rig.pose.bones}
def put(p):
 action(None)
 for n,(q,l,s)in p.items():
  b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=s
 bpy.context.view_layer.update()
def sample(a,f):
 action(a);sc.frame_set(int(f),subframe=float(f%1));return get()
def rot(n,R):
 b=rig.pose.bones[n];m=R.to_4x4();m.translation=b.head;b.matrix=m;bpy.context.view_layer.update()
def aim(n,c,v):
 b=rig.pose.bones[n];rot(n,(rig.pose.bones[c].head-b.head).rotation_difference(v).to_matrix()@b.matrix.to_3x3())
def ik(names,T,pole):
 U,F,H=names;u,f,h=[rig.pose.bones[n]for n in names];A=u.head.copy();a=(f.head-A).length;b=(h.head-f.head).length
 d=min((T-A).length,(a+b)*.999);v=(T-A).normalized();p=(pole-v*pole.dot(v)).normalized();c=float(np.clip((a*a+d*d-b*b)/(2*a*d),-1,1))
 E=A+a*(v*c+p*math.sqrt(1-c*c));aim(U,F,E-A);aim(F,H,T-rig.pose.bones[F].head)
def ease(x):
 x=float(np.clip(x,0,1));return float(np.clip(x*x*x*(10+x*(-15+6*x)),0,1))
def frame(f,n):
 f=f.normalized();n=(n-f*n.dot(f)).normalized();return Matrix((f.cross(n),f,n)).transposed()
rb=rig.data.bones
R0={n:b.matrix_local.to_3x3().copy()for n,b in rb.items()}
M0={n:b.matrix_local.copy()for n,b in rb.items()}
old={a.name:[sample(a,f)for f in range(int(a.frame_range[1])+1)]for a in list(bpy.data.actions)}
old['Running']=old['SourceRun']
sources={}
for role in ['SourceIdle','SourceHit','SourceShot','SourceDeath']:
 a=bpy.data.actions[role];sources[role]=[]
 for f in range(int(a.frame_range[1])+1):
  sample(a,f);sources[role].append({n:b.matrix.copy()for n,b in rig.pose.bones.items()})
action(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();neutral=get()
normalR=Vector(json.loads((P/'work/cast_intent.json').read_text())['palm_normal_hand_local'])
fwdR=(rb['B_R_Hand'].matrix_local.inverted()@rb['B_R_Finger2'].head_local).normalized()
palmframe=frame(fwdR,normalR)
G=M0['B_L_Hand'].inverted()@M0['Bow']
# The native bow spans outward/forward with the string above the stave.
z=Vector((-.35,.937,0)).normalized();y=Vector((0,0,1));carryR=Matrix((y.cross(z),y,z)).transposed()
drawR=Matrix.Rotation(math.radians(12),3,'Z')@Matrix.Rotation(math.pi,3,'Y')
feet={};pv=np.array([x.value for x in body.data.attributes['piece'].data]);gn={g.index:g.name for g in body.vertex_groups}
for side in 'LR':
 ft=rb[f'B_{side}_Foot'];ids=[v.index for v in body.data.vertices if v.co.z<.13 and sum(g.weight for g in v.groups if gn[g.group]in[f'B_{side}_Foot',f'B_{side}_Toe0'])>.55]
 pts=np.array([tuple(body.data.vertices[i].co)for i in ids]);front=pts[pts[:,1]<np.percentile(pts[:,1],20)].mean(0);v=Vector(front)-ft.head_local;v.z=0;v.normalize();Q=Matrix.Rotation(-math.atan2(v.x,-v.y),3,'Z')
 feet[side]={'R':Q@R0[ft.name],'height':-min((Q@(Vector(p)-ft.head_local)).z for p in pts)+.001,'ids':ids}
def arm(side,T,pole,Hrot=None,palm=None,natural=None):
 U,F,H=[f'B_{side}_{n}'for n in ['UpperArm','Forearm','Hand']]
 if pole is None:
  parent=rb[U].parent.name;hinge=rig.pose.bones[parent].matrix.to_3x3()@R0[parent].inverted()@R0[U]@Vector((0,0,-1));pole=(T-rig.pose.bones[U].head).normalized().cross(hinge)
 ik([U,F,H],T,pole);u=(rig.pose.bones[F].head-rig.pose.bones[U].head).normalized();v=(rig.pose.bones[H].head-rig.pose.bones[F].head).normalized()
 keepF=rig.pose.bones[F].matrix.copy();keepH=rig.pose.bones[H].matrix.copy();normal=u.cross(v).normalized();m=rig.pose.bones[U].matrix.to_3x3();oldn=-m.col[2];oldn=(oldn-u*oldn.dot(u)).normalized()
 ang=math.atan2(u.dot(oldn.cross(normal)),oldn.dot(normal));rot(U,Quaternion(u,ang).to_matrix()@m);rig.pose.bones[F].matrix=keepF;bpy.context.view_layer.update();rig.pose.bones[H].matrix=keepH;bpy.context.view_layer.update()
 # Minimal hinge swing gives a neutral forearm frame. Share required palm roll with the wrist.
 neutralF=rig.pose.bones[U].matrix.to_3x3()@R0[U].inverted()@R0[F]
 localv=R0[F].inverted()@(rb[H].head_local-rb[F].head_local).normalized()
 Frot=(neutralF@localv).rotation_difference(v).to_matrix()@neutralF
 if natural is not None:
  Frot=Quaternion(v,(rest_roll if side=='R'else 0)*(1-natural)).to_matrix()@Frot
  Hrot=Frot@R0[F].inverted()@R0[H]@(rest_wrist.slerp(Quaternion(),natural).to_matrix() if side=='R'else Matrix.Identity(3))
  rot(F,Frot);rot(H,Hrot)
  rig.pose.bones[f'B_{side}_ForearmTwist'].rotation_quaternion=Quaternion();rig.pose.bones[f'B_{side}_UpperArmTwist'].rotation_quaternion=Quaternion()
  bpy.context.view_layer.update();return
 if Hrot is None:Hrot=frame(v,palm)@palmframe.inverted()
 neutralH=Frot@R0[F].inverted()@R0[H];q=neutralH.to_quaternion().inverted()@Hrot.to_quaternion()
 axis=R0[H].inverted()@(sum((rb[f'B_{side}_Finger{i}'].head_local for i in [0,1,2,2,4]),Vector())/5-rb[H].head_local).normalized()
 twist=math.remainder(2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w),math.tau)
 share=float(np.clip(twist*.8,-math.radians(85),math.radians(85)))
 rot(F,Quaternion(v,share).to_matrix()@Frot);rot(H,Hrot)
 rig.pose.bones[f'B_{side}_ForearmTwist'].rotation_quaternion=Quaternion()
 rig.pose.bones[f'B_{side}_UpperArmTwist'].rotation_quaternion=Quaternion()
 bpy.context.view_layer.update()
def ground(targets):
 correction=0
 for side,T in targets.items():
  th,ca,ft=[rig.pose.bones[f'B_{side}_{n}']for n in ['Thigh','Calf','Foot']];a=(ca.head-th.head).length+(ft.head-ca.head).length
  xy=Vector((T.x-th.head.x,T.y-th.head.y,0)).length
  correction=max(correction,th.head.z-T.z-math.sqrt(max(.01,(a*.995)**2-xy*xy)))
 if correction>0:
  b=rig.pose.bones['B_Pelvis'];m=b.matrix.copy();m.translation.z-=correction;b.matrix=m;bpy.context.view_layer.update()
 for side,T in targets.items():
  ik([f'B_{side}_{n}'for n in ['Thigh','Calf','Foot']],T,Vector((0,-1,0)));rot(f'B_{side}_Foot',feet[side]['R']);rig.pose.bones[f'B_{side}_Toe0'].rotation_quaternion=Quaternion()
 bpy.context.view_layer.update()
def strings(nock=None,visible=False):
 bm=rig.pose.bones['Bow'].matrix;mid=bm@Vector((0,.215,.04));nock=nock if nock is not None else mid
 for name,z in [('StringTop',.55),('StringBottom',-.55)]:
  tip=bm@Vector((0,.215,z));d=nock-tip;base=bm.to_quaternion()@Quaternion((1,0,0),math.pi if name=='StringTop'else 0);q=(base@Vector((0,0,1))).rotation_difference(d)@base;m=q.to_matrix().to_4x4();m.translation=tip;rig.pose.bones[name].matrix=m@Matrix.Scale(d.length,4)@M0[name]
 d=(bm@Vector((0,-.08,-.06))-nock)if visible else Vector((0,-1,0));m=d.to_track_quat('Z','Y').to_matrix().to_4x4();m.translation=nock;b=rig.pose.bones['Arrow'];b.matrix=m@Matrix.Scale(1.22,4)@Matrix.Translation((0,0,.32))@M0['Arrow']
 if not visible:b.scale*=.001
 bpy.context.view_layer.update()
def rest(f=0):
 put(neutral)
 for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
  ref=sources['SourceIdle'][0][n].to_quaternion();cur=sources['SourceIdle'][int(f)%60][n].to_quaternion();delta=cur@ref.inverted();rot(n,Quaternion().slerp(delta,.35).to_matrix()@R0[n])
 ground({s:Vector((.225 if s=='L'else-.225,0,feet[s]['height']))for s in 'LR'})
 for n,(q,l,sz)in old['Standing'][0].items():
  if n.startswith('B_L_Finger'):b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=sz
 arm('R',Vector((-.315,-.01,.925)),Vector((-.12,.15,0)),palm=Vector((1,0,0)))
 arm('L',Vector((.365,-.13,.96)),Vector((.1,.1,0)),Hrot=carryR@G.to_3x3().inverted())
 rig.pose.bones['Bow'].matrix_basis.identity();strings()
rest();home=get()
rf=rig.pose.bones['B_R_Forearm'].matrix.to_3x3();rh=rig.pose.bones['B_R_Hand'].matrix.to_3x3();ru=rig.pose.bones['B_R_UpperArm'].matrix.to_3x3()
axis=R0['B_R_Forearm'].inverted()@(rb['B_R_Hand'].head_local-rb['B_R_Forearm'].head_local).normalized()
q=(ru@R0['B_R_UpperArm'].inverted()@R0['B_R_Forearm']).to_quaternion().inverted()@rf.to_quaternion()
rest_roll=math.remainder(2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w),math.tau)
rest_wrist=(rf@R0['B_R_Forearm'].inverted()@R0['B_R_Hand']).to_quaternion().inverted()@rh.to_quaternion()
homemats={n:b.matrix.copy()for n,b in rig.pose.bones.items()}
output={};report={'source_idle':'humanoid_set/Relax.glb:RelaxIdle','source_run':'humanoid_set/Unarmed.glb:UnarmedRunForward','source_attack':'mixamo/Shooting Arrow.fbx','source_hit':'humanoid_set/Unarmed.glb:UnarmedGetHitF1','source_death':'mixamo/packs/Pro Longbow Pack/standing death backward 01.fbx','release_s':.734375,'native_rest':{},'poses':{}}
report['native_rest']={n:{'head':list(homemats[n].translation),'rotation':[list(v)for v in homemats[n].to_3x3()]}for n in ['B_Pelvis','B_Spine2','B_L_UpperArm','B_R_UpperArm','B_L_Hand','B_R_Hand','B_L_Foot','B_R_Foot','Bow']}
for role,N in [('Standing',60),('Fidget',60),('Walking',24),('Running',24),('Hit',15),('Attack',51),('Death',120)]:
 rows=[];trace=[]
 for f in range(N+1):
  t=f/30;rest(f if role in ['Standing','Fidget']else 0)
  if role in ['Walking','Running']:
   w=ease(f/3)*(1-ease((f-(N-2))/2))
   put({n:(home[n][0].slerp(q,w),home[n][1].lerp(l,w),home[n][2].lerp(sz,w))for n,(q,l,sz)in old[role][f].items()});targets={side:rig.pose.bones[f'B_{side}_Foot'].head.copy()for side in 'LR'}
   if role=='Running':
    lift=max(0,min(T.z-feet[side]['height']for side,T in targets.items()))
    for T in targets.values():T.z-=lift
   pel=rig.pose.bones['B_Pelvis'];m=pel.matrix.copy();m.translation.x*=.35;m.translation.y=0;m.translation.z=(homemats['B_Pelvis'].translation.z-.025+.015*math.cos(math.tau*f/N))if role=='Running'else m.translation.z+.018;pel.matrix=m;bpy.context.view_layer.update()
   for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
    R=rig.pose.bones[n].matrix.to_3x3();D=R@R0[n].inverted();e=D.to_euler('XYZ');e.z*=.20*w;e.x*=.3*w;e.y*=.3*w
    if role=='Walking' and n!='B_Pelvis':
     # Smooth absolute trunk frames avoid recursively attenuating already changed parent rotations.
     phase=math.tau*f/N;envelope=math.sin(math.pi*f/N)**2
     fraction={'B_Spine':.35,'B_Spine1':.7,'B_Spine2':1,'B_Neck':1,'B_Head':1}[n]
     e.x=math.radians(1.5)*envelope;e.y=math.radians(.8)*math.sin(phase)*envelope
     e.z=math.radians(-2)*math.sin(phase)*envelope*fraction
    rot(n,e.to_matrix()@R0[n])
   w=ease(f/3)*(1-ease((f-(N-2))/2))
   for side,T in targets.items():
    T.x=.225 if side=='L'else-.225
    if role=='Running':T.y=float(np.clip(T.y*.55,-.18,.18));T.z=feet[side]['height']+min(.12,max(0,T.z-feet[side]['height']))
    T.z=max(feet[side]['height'],T.z-.008);T.z+=max(0,T.z-feet[side]['height'])*(.12 if side=='R'else 0);targets[side]=homemats[f'B_{side}_Foot'].translation.lerp(T,w)
   m=rig.pose.bones['B_Pelvis'].matrix.copy();m.translation=homemats['B_Pelvis'].translation.lerp(m.translation,w);rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
   ground(targets)
   dz=rig.pose.bones['B_Pelvis'].head.z-homemats['B_Pelvis'].translation.z
   swing=math.sin(math.tau*f/N)*(.035 if role=='Walking'else .06)*w
   for n,(q,l,sz)in home.items():
    if 'Finger'in n:b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=sz
   arm('R',Vector((-.315-.03*w if role=='Running'else -.315,-.01+swing,.925+dz)),Vector((-.12,.15,0)),palm=Vector((1,0,0)))
   arm('L',Vector((.365,-.13-swing*.25,.96+dz)),Vector((.1,.1,0)),Hrot=carryR@G.to_3x3().inverted())
   rig.pose.bones['Bow'].matrix_basis.identity();strings()
  elif role=='Fidget':
   k=math.sin(math.tau*f/N)**2
   n='B_Head';rot(n,Matrix.Rotation(math.radians(8)*k,3,'Z')@rig.pose.bones[n].matrix.to_3x3())
   arm('R',homemats['B_R_Hand'].translation+Vector((-.005*k,-.01*k,.01*k)),Vector((-.12,.15,0)),palm=Vector((1,0,0)))
   arm('L',homemats['B_L_Hand'].translation+Vector((.015*k,-.02*k,.015*k)),Vector((.1,.1,0)),Hrot=carryR@G.to_3x3().inverted())
   rig.pose.bones['Bow'].matrix_basis.identity();strings()
  elif role=='Hit':
   w=ease(f/5)*(1-ease((f-8)/7));src=sources['SourceHit'][f];base=sources['SourceHit'][0]
   for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
    delta=src[n].to_quaternion()@base[n].to_quaternion().inverted();e=delta.to_euler('XYZ');e.x=-abs(e.x)*.5*w-math.radians(14)*w;e.y*=.12*w;e.z*=.12*w;rot(n,e.to_matrix()@homemats[n].to_3x3())
   p=rig.pose.bones['B_Pelvis'];m=p.matrix.copy();m.translation+=Vector((0,.035*math.sin(math.pi*f/N)**2,-.025*math.sin(math.pi*f/N)**2));p.matrix=m;bpy.context.view_layer.update()
   ground({s:homemats[f'B_{s}_Foot'].translation.copy()for s in 'LR'})
   sway=.065*math.sin(math.pi*f/N)**2
   arm('R',Vector((-.315-.025*w,-.01+sway,.925+sway*.35)),Vector((-.1,.12,0)),palm=Vector((1,0,0)))
   arm('L',Vector((.365,-.13+sway,.96+sway*.35)),Vector((.1,.1,0)),Hrot=carryR@G.to_3x3().inverted());rig.pose.bones['Bow'].matrix_basis.identity();strings()
  elif role=='Attack':
   raise_w=ease(t/.63);recover=1-ease((t-.9)/.8);w=raise_w*recover
   sf=min(150,60+f*2);src=sources['SourceShot'][sf]
   for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2']:
    D=src[n].to_3x3()@R0[n].inverted();e=D.to_euler('XYZ');e.x*=.35*w;e.y*=.35*w;cap={'B_Pelvis':32,'B_Spine':45,'B_Spine1':58,'B_Spine2':72}[n];e.z=float(np.clip(e.z,-math.radians(cap),math.radians(cap)))*w;rot(n,e.to_matrix()@R0[n])
   ground({s:homemats[f'B_{s}_Foot'].translation.copy()for s in 'LR'})
   for n in ['B_Neck','B_Head']:rot(n,R0[n])
   left=Vector((.365,-.13,.96)).lerp(Vector((-.10,-.635,1.385)),w)
   left.x+=.20*math.sin(math.pi*w);left.y-=.25*math.sin(math.pi*w)
   bowR=carryR.to_quaternion().slerp(drawR.to_quaternion(),w).to_matrix()
   arm('L',left,Vector((.1,.1,0)).lerp(Vector((.35,.1,-1)),w),Hrot=bowR@G.to_3x3().inverted())
   # Straight drawing wrist at the cheek; follow-through stays beside the jaw.
   right=Vector((-.315,-.01,.925)).lerp(Vector((-.23,-.035,1.415)),w)
   right.x-=.10*math.sin(math.pi*w);right.y-=.07*math.sin(math.pi*w)
   right.y+=.045*ease((t-.734375)/.16)*recover
   Hdraw=frame(Vector((0,-1,0)),Vector((1,0,0)))@palmframe.inverted()
   Hr=homemats['B_R_Hand'].to_quaternion().slerp(Hdraw.to_quaternion(),w).to_matrix()
   arm('R',right,Vector((-.12,.15,0)).lerp(Vector((-.2,1,-.15)),w),palm=Vector((1,0,0)),natural=w)
   rig.pose.bones['Bow'].matrix_basis.identity();bpy.context.view_layer.update()
   # Keep relaxed hooked fingers: no source fist or backward wrist is carried into the draw.
   for n,(q,l,sz)in home.items():
    if n.startswith('B_R_Finger'):b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=sz
   bpy.context.view_layer.update()
   finger=rig.pose.bones['B_R_Finger11'].head.lerp(rig.pose.bones['B_R_Finger12'].head,.55);bm=rig.pose.bones['Bow'].matrix;mid=bm@Vector((0,.215,.04))
   draw=ease((t-.32)/.24)*(1-ease((t-(.734375-1/60))/(1/30)));strings(mid.lerp(finger,draw),.56<=t<.734375)
  elif role=='Death':
   sf=f*.75;lo=int(sf);hi=min(90,lo+1);a=old['SourceDeath'][lo];b=old['SourceDeath'][hi];target={n:(v[0].slerp(b[n][0],sf-lo),v[1].lerp(b[n][1],sf-lo),v[2].lerp(b[n][2],sf-lo))for n,v in a.items()};w=ease(f/25)
   put({n:(home[n][0].slerp(v[0],w),home[n][1].lerp(v[1],w),home[n][2].lerp(v[2],w))for n,v in target.items()})
   root=rig.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.x*=.25;m.translation.y=.02+(m.translation.y-.02)*.25;root.matrix=m;bpy.context.view_layer.update()
   if f==0:put(home)
   D=rig.pose.bones['B_Spine2'].matrix@homemats['B_Spine2'].inverted()
   for n in ['B_Neck','B_Head']:rot(n,D.to_3x3()@R0[n])
   fall=ease((f-25)/40)
   # Keep the anatomical rest rotations while the library fall spreads both arms for balance.
   for side in 'LR':
    clav=f'B_{side}_Clavicle'
    if clav in rig.pose.bones:rot(clav,D.to_3x3()@homemats[clav].to_3x3())
    U,F,H=[f'B_{side}_{n}'for n in ['UpperArm','Forearm','Hand']]
    for name in [U,F,H,f'B_{side}_UpperArmTwist',f'B_{side}_ForearmTwist']:
     q,l,sz=home[name];bone=rig.pose.bones[name];bone.rotation_quaternion=q;bone.location=l;bone.scale=sz
    bpy.context.view_layer.update()
    rot(U,D.to_3x3()@Matrix.Rotation(math.radians(65 if side=='L'else -65)*ease((f-5)/35),3,Vector((0,-1,0)))@homemats[U].to_3x3())
   for n,(q,l,sz)in home.items():
    if 'Finger'in n:b=rig.pose.bones[n];b.rotation_quaternion=q.slerp(Quaternion(),ease((f-30)/9))if n.startswith('B_L_')else q;b.location=l;b.scale=sz
   rig.pose.bones['Bow'].matrix_basis.identity();bpy.context.view_layer.update()
   if f==30:drop_start=rig.pose.bones['Bow'].matrix.copy()
   if f>30:
    drop=ease((f-30)/24);out=float(np.clip((f-30)/9,0,1));down=ease((f-34)/24)
    m=drop_start.to_quaternion().slerp(carryR.to_quaternion(),drop).to_matrix().to_4x4();m.translation=drop_start.translation.lerp(Vector((.85,.25,.023)),out);m.translation.z=drop_start.translation.z*(1-down)+.023*down;rig.pose.bones['Bow'].matrix=m
   strings()
   tail_turn=Matrix.Rotation(math.radians(-65)*fall,3,'Z')
   for n in ['Tail0','Tail1','Tail2']:rot(n,(D.to_quaternion().slerp(tail_turn.to_quaternion(),fall).to_matrix())@R0[n])
  # The short loin flap follows the leading thigh without twisting the waist seam.
  if True:
   b=rig.pose.bones['LoinFlap'];b.matrix_basis.identity();bpy.context.view_layer.update()
   D=rig.pose.bones['B_Pelvis'].matrix@M0['B_Pelvis'].inverted();inv=D.to_3x3().inverted();angles=[]
   for s in 'LR':
    v=inv@(rig.pose.bones[f'B_{s}_Calf'].head-rig.pose.bones[f'B_{s}_Thigh'].head);angles.append(math.atan2(-v.y,-v.z))
   angle=max(0,max(angles))+math.radians(8);pivot=rb['LoinFlap'].head_local;b.matrix=D@Matrix.Translation(pivot)@Matrix.Rotation(-angle,4,'X')@Matrix.Translation(-pivot)@M0['LoinFlap']
  rows.append(get());trace.append({n:list(rig.pose.bones[n].head)for n in ['B_Pelvis','B_L_UpperArm','B_R_UpperArm','B_L_Hand','B_R_Hand','B_R_Forearm','Bow']})
 output[role]=rows;report['poses'][role]=trace
output['Cast']=output['Attack'];output['Dead']=[output['Death'][-1]]*31
action(None)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for role,rows in output.items():
 a=bpy.data.actions.new(role);a.use_fake_user=True;action(a);prev={}
 for f,row in enumerate(rows):
  for n,(q,l,s)in row.items():
   if n in prev and prev[n].dot(q)<0:q=-q
   prev[n]=q;b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=s
   for channel in ['rotation_quaternion','location','scale']:b.keyframe_insert(channel,frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
# Keep the two string segments joined to one nock through the fractional release.
for role in ['Attack','Cast']:
 a=bpy.data.actions[role];action(a);previous={}
 times=sorted(set([float(t)for t in np.arange(0,1.70001,1/120)]+[.734375+i/480 for i in range(-10,11)]+[.734375,1.7]))
 for t in times:
  f=t*30;sc.frame_set(int(f),subframe=f%1);bm=rig.pose.bones['Bow'].matrix.copy();mid=bm@Vector((0,.215,.04));finger=rig.pose.bones['B_R_Finger11'].head.lerp(rig.pose.bones['B_R_Finger12'].head,.55)
  draw=ease((t-.32)/.24)*(1-ease((t-(.734375-1/60))/(1/30)));strings(mid.lerp(finger,draw),.56<=t<.734375)
  for name in ['StringTop','StringBottom','Arrow']:
   bone=rig.pose.bones[name];q=bone.rotation_quaternion.copy()
   if name in previous and previous[name].dot(q)<0:q.negate();bone.rotation_quaternion=q
   previous[name]=q
   for channel in ['rotation_quaternion','location','scale']:bone.keyframe_insert(channel,frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
action(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round5/motion.blend'))
(P/'work/round5/authoring_intent.json').write_text(json.dumps(report,indent=2))
