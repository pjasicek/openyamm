"""Fit the owned Jogging cycle to the unchanged 1.2 m runtime stride binding."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];W=P/'work/round5';R=P/'review/round5'
bpy.ops.wm.open_mainfile(filepath=str(W/'jog_source.blend'))
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
src=[sample(bpy.data.actions['JogSource'],.5+26*i/96)for i in range(97)]
# Distribute the source cycle's small endpoint drift, retaining its swing throughout.
ends={n:src[-1][n][0].rotation_difference(src[0][n][0])for n in NAMES}
for i,p in enumerate(src):
 for n,(q,l)in list(p.items()):p[n]=(q@Quaternion().slerp(ends[n],i/96),l)
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
# Phase follows the source left-leg reach; the right leg is half a cycle behind.
ys=[]
for p in src[:-1]:apply(p);ys.append(world('B_L_Foot').translation.y)
phase0=(-int(np.argmin(ys))/96)%1
frames=[];targets_report=[]
for i,p0 in enumerate(src):
 p=dict(p0)
 for n in ['B_L_UpperArm','B_L_Forearm']:p[n]=(rest[n][0].slerp(p[n][0],.45),rest[n][1])
 for n in NAMES:
  if 'Hand' in n or 'Finger' in n or n in ['Axe','Shield']  :p[n]=rest[n]
  if 'Toe' in n:p[n]=(Quaternion(),Vector())
 apply(p)
 # Keep genuine torso and arm swing; carry the broad props beside the cuirass.
 for sd in 'LR':
  n=f'B_{sd}_UpperArm';M=world(n);t=M.translation.copy();M=Matrix.Rotation(math.radians(9 if sd=='R'else -10),4,'Y')@M;M.translation=t;put(n,M)
 targets={}
 for sd in 'LR':
  phase=(i/96+phase0+(0 if sd=='L'else .5))%1;stance=.47;stride=1.2*1.55;travel=stride*stance
  if phase<stance:y=-travel/2+stride*phase;lift=0
  else:
   u=(phase-stance)/(1-stance);h=u*u*(3-2*u)
   y=travel/2*(1-2*h)+stride*(1-stance)*(2*u**3-3*u*u+u)
   lift=.14*math.sin(math.pi*u)**1.25
  Q=flat[sd];T=Vector((width[sd],y,.031+lift-min((Q@v).z for v in sole[sd])));targets[sd]=(T,Q)
 pel=world('B_Pelvis');pel.translation=Vector((0,0,.985+.012*math.cos(4*math.pi*(i/96+phase0))))
 put('B_Pelvis',pel)
 for sd,(T,Q)in targets.items():
  H=world(f'B_{sd}_Thigh').translation;reach=sum(lens[sd])-.006;xy=(T.x-H.x)**2+(T.y-H.y)**2
  assert xy<reach*reach
  pel.translation.z=min(pel.translation.z,T.z+math.sqrt(reach*reach-xy)+pel.translation.z-H.z)
 put('B_Pelvis',pel)
 for sd,(T,Q)in targets.items():
  th,ca,ft=[f'B_{sd}_{n}'for n in ['Thigh','Calf','Foot']];H=world(th).translation;a,b=lens[sd];d=(T-H).length;assert abs(a-b)<d<a+b
  u=(T-H).normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);K=H+a*(u*c+v*math.sqrt(max(0,1-c*c)))
  aim(th,ca,K-H);aim(ca,ft,T-K);M=Q.to_matrix().to_4x4();M.translation=T;put(ft,M)
 for sd in 'LR':
  un,fn,hn=[f'B_{sd}_{n}'for n in ['UpperArm','Forearm','Hand']];U,F,H=[world(n)for n in [un,fn,hn]]
  u=(F.translation-U.translation).normalized();v=(H.translation-F.translation).normalized();hinge=U.to_3x3()@Vector((0,0,-1));target=u.cross(v).normalized();hinge=(hinge-u*hinge.dot(u)).normalized()
  angle=math.atan2(u.dot(hinge.cross(target)),hinge.dot(target));M=Matrix.Rotation(angle,4,u)@U;M.translation=U.translation;put(un,M);put(fn,F);put(hn,H)
 for sd in 'LR':
  for base,child,helper,share in [('Forearm','Hand','ForearmTwist',.6),('UpperArm','Forearm','UpperArmTwist',-.5)]:
   bn=f'B_{sd}_{base}';cn=f'B_{sd}_{child}';b=rig.data.bones[bn];c=rig.data.bones[cn];axis=(b.matrix_local.inverted()@c.head_local).normalized()
   q=(rig.pose.bones[bn].matrix.inverted()@rig.pose.bones[cn].matrix).to_quaternion()@(b.matrix_local.inverted()@c.matrix_local).to_quaternion().inverted() if base=='Forearm' else rig.pose.bones[bn].rotation_quaternion
   angle=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);angle=(angle+math.pi)%(2*math.pi)-math.pi
   rig.pose.bones[f'B_{sd}_{helper}'].rotation_quaternion=Quaternion(axis,share*angle)
 bpy.context.view_layer.update();frames.append({b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones});targets_report.append({sd:list(T)for sd,(T,Q)in targets.items()})
frames[-1]=frames[0]
act(None);bpy.data.actions.remove(bpy.data.actions['Running']);a=bpy.data.actions.new('Running');a.use_fake_user=True;prev={};worlds=[]
for i,p in enumerate(frames):
 apply(p);worlds.append({b.name:[list(row)for row in rig.matrix_world@b.matrix]for b in rig.pose.bones});act(a)
 for n,(q,l)in p.items():
  if n in prev and q.dot(prev[n])<0:q=-q
  prev[n]=q;pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=i/4);pb.keyframe_insert('location',frame=i/4)
a.use_frame_range=True;a.frame_start=0;a.frame_end=24
for lay in a.layers:
 for st in lay.strips:
  for cb in st.channelbags:
   for fc in cb.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.render.fps=30
(W/'running_world.json').write_text(json.dumps({'times':list(np.linspace(0,.8,97)),'poses':worlds,'rest':{b.name:[list(row)for row in rig.matrix_world@b.matrix_local]for b in rig.data.bones}}))
(R/'motion_fit.json').write_text(json.dumps({'source':'anim_library/mixamo/Jogging.fbx','source_cycle_frames':[.5,26.5],'source_fps':30,'duration_s':.8,'sample_hz':120,'stride_binding_m':1.2,'runtime_run_multiplier':1.55,'fitted_stride_m':1.86,'nominal_speed_m_s':2.325,'stance_fraction':.47,'swing_lift_m':.14,'phase_offset':phase0,'foot_targets':targets_report},indent=2))
act(bpy.data.actions['Standing']);scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(W/'running_author.blend'))
print('RUNNING_FIT_READY',flush=True)
