"""Fit the owned Standard Run cycle to the unchanged 1.2 m runtime stride binding."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];W=P/'work/round6';R=P/'review/round6'
bpy.ops.wm.open_mainfile(filepath=str(W/'run_source.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
NAMES=[b.name for b in rig.pose.bones]
def act(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 act(a);scene.frame_set(int(f),subframe=f%1)
 return {b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones}
def apply(p):
 act(None)
 for n,(q,l)in p.items():
  b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l;b.scale=(1,1,1)
 bpy.context.view_layer.update()
def world(n):return rig.matrix_world@rig.pose.bones[n].matrix
def put(n,M):rig.pose.bones[n].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
def aim(n,ch,d):
 M=world(n);u=world(ch).translation-M.translation;Q=u.normalized().rotation_difference(d.normalized());t=M.translation.copy();M=Q.to_matrix().to_4x4()@M;M.translation=t;put(n,M)
rest=sample(bpy.data.actions['Standing'],0)
src=[sample(bpy.data.actions['RunSource'],22*i/88)for i in range(89)]
# Distribute the source cycle's small endpoint drift, retaining its swing throughout.
ends={n:src[-1][n][0].rotation_difference(src[0][n][0])for n in NAMES}
for i,p in enumerate(src):
 for n,(q,l)in list(p.items()):p[n]=(q@Quaternion().slerp(ends[n],i/88),l)
act(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
sole={};flat={};width={};lens={};home={}
for sd in 'LR':
 names={f'B_{sd}_Foot',f'B_{sd}_Toe0'};groups={g.index for g in body.vertex_groups if g.name in names}
 ids=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.5]
 low=min(body.data.vertices[i].co.z for i in ids);ids=[i for i in ids if body.data.vertices[i].co.z<low+.006]
 M=rig.matrix_world@rig.data.bones[f'B_{sd}_Foot'].matrix_local
 pts=[body.matrix_world@body.data.vertices[i].co for i in ids];assert len(pts)>5
 sole[sd]=[M.inverted()@p for p in pts]
 xy=np.array([tuple(p)[:2]for p in pts]);axis=xy[xy[:,1]<=np.quantile(xy[:,1],.3)].mean(0)-xy[xy[:,1]>=np.quantile(xy[:,1],.7)].mean(0)
 if axis[1]>0:axis=-axis
 yaw=math.atan2(axis[0],-axis[1]);flat[sd]=Quaternion((0,0,1),-yaw)@M.to_quaternion();width[sd]=M.translation.x
 H,K,A=[rig.matrix_world@rig.data.bones[f'B_{sd}_{n}'].head_local for n in ['Thigh','Calf','Foot']];lens[sd]=((K-H).length,(A-K).length)
print('SOLE_FIT',width,lens,flush=True)
# Library cycle, smoothed periodically before fitting; no framewise root clamp.
raw=[dict(p) for p in src[:-1]];kernel=np.exp(-.5*(np.arange(-4,5)/1.4)**2);kernel/=kernel.sum()
for i in range(88):
 for n in NAMES:
  q=raw[i][n][0];v=np.zeros(4)
  for k,w in zip(range(-4,5),kernel):
   x=raw[(i+k)%88][n][0];v+=np.array(x)*w*(1 if x.dot(q)>=0 else -1)
  src[i][n]=(Quaternion(v).normalized(),raw[i][n][1])
src[-1]=src[0]
# Reuse the shared skin/sole evaluator during FOOT fitting, never adjust the root after this.
sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as g
config=json.loads((P/'gates.json').read_text());gb=g.Glb(P/'review/round6/before/export/mm6_figc.glb');meshes=[m for m in g.load_meshes(gb)if '/colour' in m.label]
for m in meshes:g.configure_mesh(m,config,g.Report(config))
ys=[]
for p in src[:-1]:apply(p);ys.append(world('B_L_Foot').translation.y)
phase0=(-int(np.argmin(ys))/88)%1
stance=.48;stride=1.86;duration=22/30;amplitude=.012

def foot_target(sd,phase):
 travel=stride*stance;lift=0;pitch=0
 if phase<stance:y=-travel/2+stride*phase
 else:
  u=(phase-stance)/(1-stance);h=u**3*(10-15*u+6*u*u)
  y=travel/2+stride*(1-stance)*u-stride*h
  lift=.23*math.sin(math.pi*u)**2;pitch=math.radians(38)*math.sin(math.pi*u)**2
 Q=Quaternion((1,0,0),pitch)@flat[sd]
 return Vector((width[sd],y,.025+lift-min((Q@v).z for v in sole[sd]))),Q,lift

def leg(sd,T,Q):
 th,ca,ft=[f'B_{sd}_{n}'for n in ['Thigh','Calf','Foot']];H=world(th).translation;a,b=lens[sd];d=(T-H).length;assert abs(a-b)<d<a+b,(sd,d,a+b)
 u=(T-H).normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);K=H+a*(u*c+v*math.sqrt(max(0,1-c*c)))
 aim(th,ca,K-H);aim(ca,ft,T-K);M=Q.to_matrix().to_4x4();M.translation=T;put(ft,M)

def prepared(i):
 p=dict(src[i])
 for n in NAMES:
  if 'Hand' in n or 'Finger' in n or n in ['Axe','Shield']:p[n]=rest[n]
  if 'Toe' in n:p[n]=(Quaternion(),Vector())
  if n=='B_Pelvis':p[n]=(rest[n][0].slerp(p[n][0],.25),rest[n][1])
  if n.startswith('B_Spine') or n in ['B_Neck','B_Head']:p[n]=(rest[n][0].slerp(p[n][0],.65),rest[n][1])
 for n in ['B_L_UpperArm','B_L_Forearm']:p[n]=(rest[n][0].slerp(p[n][0],.55),rest[n][1])
 return p
# Find ONE tallest feasible baseline for the whole cycle and both legs. Retain 2 cm reach reserve for sole fitting.
limits=[]
for i in range(89):
 apply(prepared(i));phase=(i/88+phase0)%1;bob=amplitude*math.cos(4*math.pi*(phase-stance));pel=world('B_Pelvis');pel.translation=Vector((0,0,.9));put('B_Pelvis',pel)
 for sd in 'LR':
  T,Q,lift=foot_target(sd,(phase+(0 if sd=='L'else .5))%1);H=world(f'B_{sd}_Thigh').translation;reach=sum(lens[sd])-.020;xy=(T.x-H.x)**2+(T.y-H.y)**2
  limits.append(T.z+math.sqrt(reach*reach-xy)+.9-H.z-bob)
baseline=min(limits);print('SMOOTH_PELVIS_BASE',baseline,flush=True)
frames=[];sole_corrections=[]
for i in range(89):
 p=prepared(i);apply(p);phase=(i/88+phase0)%1
 for sd in 'LR':
  n=f'B_{sd}_UpperArm';M=world(n);t=M.translation.copy();M=Matrix.Rotation(math.radians(22 if sd=='R'else -10),4,'Y')@M;M.translation=t;put(n,M)
 pel=world('B_Pelvis');pel.translation=Vector((0,0,baseline+amplitude*math.cos(4*math.pi*(phase-stance))));put('B_Pelvis',pel)
 targets={sd:foot_target(sd,(phase+(0 if sd=='L'else .5))%1)for sd in 'LR'}
 for sd,(T,Q,lift)in targets.items():leg(sd,T,Q)
 corrections={sd:0 for sd in 'LR'}
 for iteration in range(5):
  matrices=gb.rest.copy()
  for pb in rig.pose.bones:matrices[gb.names[pb.name]]=np.array(world(pb.name))
  lows={sd:[]for sd in 'LR'}
  for m in meshes:
   points=m.posed(matrices)
   for sd,(ids,heel,toe)in m.feet.items():
    lows[sd].append(float(points[ids,2].min()))
    if m is meshes[0]:
     direction=points[heel].mean(0)-points[toe].mean(0);actual=math.atan2(direction[2],np.linalg.norm(direction[:2]));ph=(phase+(0 if sd=='L'else .5))%1;desired=0 if ph<stance else math.radians(38)*math.sin(math.pi*(ph-stance)/(1-stance))**2
     T,Q,lift=targets[sd];Q=Quaternion((0,0,1),math.atan2(direction[0],direction[1]))@Quaternion((1,0,0),desired-actual)@Q;targets[sd]=(T,Q,lift)
  for sd,(T,Q,lift)in targets.items():
   dz=config['floor_m']-.0012+lift-min(lows[sd]);T.z+=dz;corrections[sd]+=dz;leg(sd,T,Q)
 sole_corrections.append(corrections)
 for sd in 'LR':
  un,fn,hn=[f'B_{sd}_{n}'for n in ['UpperArm','Forearm','Hand']];U,F,H=[world(n)for n in [un,fn,hn]]
  u=(F.translation-U.translation).normalized();v=(H.translation-F.translation).normalized();hinge=U.to_3x3()@Vector((0,0,-1));target=u.cross(v).normalized();hinge=(hinge-u*hinge.dot(u)).normalized()
  angle=math.atan2(u.dot(hinge.cross(target)),hinge.dot(target));M=Matrix.Rotation(angle,4,u)@U;M.translation=U.translation;put(un,M);put(fn,F);put(hn,H)
 # Turn the carrying wrist so the shaft points outside the torso, preserving its grip frame.
 F,H=world('B_R_Forearm'),world('B_R_Hand');axis=(H.translation-F.translation).normalized();M=Matrix.Rotation(math.radians(90),4,axis)@H;M.translation=H.translation;FM=Matrix.Rotation(math.radians(80),4,axis)@F;FM.translation=F.translation;put('B_R_Forearm',FM);put('B_R_Hand',M)
 for sd in 'LR':
  for base,child,helper,share in [('Forearm','Hand','ForearmTwist',.6),('UpperArm','Forearm','UpperArmTwist',-.5)]:
   bn=f'B_{sd}_{base}';cn=f'B_{sd}_{child}';b=rig.data.bones[bn];c=rig.data.bones[cn];axis=(b.matrix_local.inverted()@c.head_local).normalized()
   q=(rig.pose.bones[bn].matrix.inverted()@rig.pose.bones[cn].matrix).to_quaternion()@(b.matrix_local.inverted()@c.matrix_local).to_quaternion().inverted()if base=='Forearm'else rig.pose.bones[bn].rotation_quaternion
   angle=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);angle=(angle+math.pi)%(2*math.pi)-math.pi;rig.pose.bones[f'B_{sd}_{helper}'].rotation_quaternion=Quaternion(axis,(-.5 if sd=='R' and base=='Forearm' else share)*angle)
 bpy.context.view_layer.update();frames.append({b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones})
frames[-1]=frames[0];act(None);bpy.data.actions.remove(bpy.data.actions['Running']);a=bpy.data.actions.new('Running');a.use_fake_user=True;prev={};worlds=[]
for i,p in enumerate(frames):
 apply(p);worlds.append({b.name:[list(row)for row in world(b.name)]for b in rig.pose.bones});act(a)
 for n,(q,l)in p.items():
  if n in prev and q.dot(prev[n])<0:q=-q
  prev[n]=q;pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=i/4);pb.keyframe_insert('location',frame=i/4)
a.use_frame_range=True;a.frame_start=0;a.frame_end=22
for lay in a.layers:
 for st in lay.strips:
  for cb in st.channelbags:
   for fc in cb.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.render.fps=30
(W/'running_world.json').write_text(json.dumps({'times':list(np.linspace(0,duration,89)),'poses':worlds,'rest':{b.name:[list(row)for row in rig.matrix_world@b.matrix_local]for b in rig.data.bones}}))
(R/'motion_fit.json').write_text(json.dumps({'source':'anim_library/mixamo/Standard Run.fbx','source_cycle_frames':[0,22],'duration_s':duration,'stride_binding_m':1.2,'run_stride_m':stride,'stance':stance,'phase_offset':phase0,'pelvis_baseline_m':baseline,'pelvis_bob_amplitude_m':amplitude,'root_floor_snaps':False,'foot_z_corrections_m':sole_corrections},indent=2))
act(bpy.data.actions['Standing']);scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(W/'running_author.blend'))
