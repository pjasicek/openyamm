"""Standard Run, with stride-matched short-leg IK and symmetric low-flight bob."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round7/run_source.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene

def act(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 act(a);scene.frame_set(int(f),subframe=f%1)
 return {b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones}
def apply(p):
 act(None)
 for n,(q,l) in p.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
rest=sample(bpy.data.actions['Standing'],0);head_rest=rig.pose.bones['B_Head'].matrix.to_quaternion()
# Pick the left heel-strike phase from the source cycle.
a=bpy.data.actions['RunSource'];end=float(a.frame_range[1]);ys=[]
for f in range(int(end)):
 sample(a,f);ys.append(rig.pose.bones['B_L_Foot'].head.y)
start=float(np.argmin(ys));src=[sample(a,(start+end*i/96)%end)for i in range(97)]
# Gentle periodic low-pass removes source key-velocity kinks without weakening the arm sweep.
raw=[dict(p)for p in src[:96]]
for j in range(96):
 for n,(q,l)in raw[j].items():
  qs=[raw[(j+k)%96][n][0]for k in range(-2,3)];v=sum((np.array(x if x.dot(q)>=0 else -x)*w for x,w in zip(qs,[.1,.2,.4,.2,.1])))
  src[j][n]=(Quaternion(v/np.linalg.norm(v)),l)
src[-1]=src[0]
old=[{n:(q.copy(),l.copy())for n,(q,l)in v.items()}for v in src]
for p in old:p['B_Pelvis']=rest['B_Pelvis']
# Measure fore/aft sole patch direction on the unchanged accepted body.
body=bpy.data.objects['Body'];sole_axes={}
for sd in 'LR':
 pts=[v.co for v in body.data.vertices if (v.co.x>0)==(sd=='L')and v.co.z<.06]
 yy=np.array([v.y for v in pts]);heel=sum((v for v in pts if v.y>=np.quantile(yy,.7)),Vector())/sum(yy>=np.quantile(yy,.7));toe=sum((v for v in pts if v.y<=np.quantile(yy,.3)),Vector())/sum(yy<=np.quantile(yy,.3))
 sole_axes[sd]=rig.data.bones[f'B_{sd}_Foot'].matrix_local.to_3x3().inverted()@(toe-heel)
sole={};flat={};lens={}
for sd in 'LR':
 n=f'B_{sd}_Foot';M=rig.data.bones[n].matrix_local
 sole[sd]=[M.inverted()@v.co for v in body.data.vertices if (v.co.x>0)==(sd=='L')and v.co.z<.008]
 apply(rest);W=rig.pose.bones[n].matrix;normal=(W.to_3x3()@M.to_3x3().inverted())@Vector((0,0,1));flat[sd]=normal.rotation_difference(Vector((0,0,1)))@W.to_quaternion()
 H,K,A=[rig.data.bones[f'B_{sd}_{k}'].head_local for k in ['Thigh','Calf','Foot']];lens[sd]=((K-H).length,(A-K).length)
def world(n):return rig.matrix_world@rig.pose.bones[n].matrix
def aim(n,child,direction):
 M=world(n);cur=world(child).translation-M.translation;R=cur.normalized().rotation_difference(direction.normalized()).to_matrix().to_4x4();t=M.translation.copy();M=R@M;M.translation=t;rig.pose.bones[n].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
def solve(sd,T,Q):
 th,ca,ft=[f'B_{sd}_{k}'for k in ['Thigh','Calf','Foot']];H=world(th).translation;a,b=lens[sd];d=(T-H).length
 assert abs(a-b)<d<a+b,('reach',i,sd,d,a+b)
 u=(T-H).normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);K=H+a*(u*c+v*math.sqrt(max(0,1-c*c)))
 aim(th,ca,K-H);M=world(ca);M.translation=K;rig.pose.bones[ca].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update();aim(ca,ft,T-K)
 M=Q.to_matrix().to_4x4();M.translation=T;rig.pose.bones[ft].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
def foot_target(sd,phase):
 stance=.44;stride=.89*1.55;travel=stride*stance
 if phase<stance:
  u=phase/stance;y=-travel/2+stride*phase;lift=0
  pitch=-10*(1-min(1,u/.14))**2+18*max(0,(u-.75)/.25)**2
 else:
  u=(phase-stance)/(1-stance);S=u*u*u*(10-15*u+6*u*u)
  # Matching stance velocity at both ends adds natural recovery overshoot without a reversal snap.
  y=travel/2-travel*S+stride*(1-stance)*(u*(1-u)**10-(1-u)*u**10)
  lift=.14*math.sin(math.pi*u)**1.25
  pitch=18*(1-u)-10*u
 Q=Quaternion(Vector((1,0,0)),math.radians(pitch))@flat[sd]
 T=Vector((.135 if sd=='L'else -.135,y,.004+lift-min((Q@v).z for v in sole[sd])))
 return T,Q
# Fit one constant centre height across the entire stride, retaining an analytic two-step bob.
pelvis_center=.70
for j,p in enumerate(old):
 apply(p);pel=world('B_Pelvis');pel.translation=Vector((0,0,0));rig.pose.bones['B_Pelvis'].matrix=rig.matrix_world.inverted()@pel;bpy.context.view_layer.update()
 for sd in 'LR':
  T,Q=foot_target(sd,(j/96+(0 if sd=='L'else .5))%1);H=world(f'B_{sd}_Thigh').translation;reach=sum(lens[sd])-.004;planar=(T.x-H.x)**2+(T.y-H.y)**2
  assert planar<reach*reach
  pelvis_center=min(pelvis_center,T.z+math.sqrt(reach*reach-planar)-H.z-.012*math.cos(4*math.pi*(j/96-.47)))
print('SYMMETRIC PELVIS CENTRE',pelvis_center,flush=True)
frames=[]
for i,p in enumerate(old):
 for n in p:
  if any(t in n for t in ['Spine','Neck','Head','Clavicle','UpperArm','Forearm']):p[n]=(src[i][n][0],rest[n][1])
  if 'Hand' in n or 'Finger' in n:p[n]=rest[n]
 apply(p)
 # Equal, smooth bob for both steps: no reach-clamping spikes in the pelvis.
 pel=world('B_Pelvis');pel.translation=Vector((0,0,pelvis_center+.012*math.cos(4*math.pi*(i/96-.47))))
 rig.pose.bones['B_Pelvis'].matrix=rig.matrix_world.inverted()@pel;bpy.context.view_layer.update()
 for sd in 'LR':
  T,Q=foot_target(sd,(i/96+(0 if sd=='L'else .5))%1);solve(sd,T,Q)
 for sd in 'LR':
  pb=rig.pose.bones[f'B_{sd}_Foot'];M=pb.matrix.copy();v=M.to_3x3()@sole_axes[sd];yaw=math.atan2(v.y,v.x);t=M.translation.copy();M=Matrix.Rotation(-math.pi/2-yaw-(math.radians(1)if sd=='R'else 0),4,'Z')@M;M.translation=t;pb.matrix=M
 bpy.context.view_layer.update()
 # Standard Run's local spine compensates for its source pelvis tilt. Restore a forward run lean.
 pb=rig.pose.bones['B_Spine'];M=pb.matrix.copy();t=M.translation.copy();neck=rig.pose.bones['B_Neck'].head;hip=rig.pose.bones['B_Pelvis'].head;trunk=neck-pb.head;desired=hip+Vector((0,-math.sin(math.radians(10)),math.cos(math.radians(10))))*(neck-hip).length-pb.head;M=trunk.normalized().rotation_difference(desired.normalized()).to_matrix().to_4x4()@M;M.translation=t;pb.matrix=M;bpy.context.view_layer.update()
 pb=rig.pose.bones['B_Head'];t=pb.matrix.translation.copy();M=(Quaternion((1,0,0),math.radians(4))@head_rest).to_matrix().to_4x4();M.translation=t;pb.matrix=M;bpy.context.view_layer.update()
 # Carry the axe outside the torso; retain source forward/back swing.
 for sd in 'LR':
  un,fn,hn=[f'B_{sd}_{n}'for n in ['UpperArm','Forearm','Hand']]
  pb=rig.pose.bones[un];M=pb.matrix.copy();t=M.translation.copy()
  M=Matrix.Rotation(math.radians(28 if sd=='R'else -15),4,'Y')@M;M.translation=t;pb.matrix=M;bpy.context.view_layer.update()
  # Rotate the upper-arm hinge onto the elbow path, preserving forearm and hand world frames.
  U=rig.pose.bones[un].matrix.copy();F=rig.pose.bones[fn].matrix.copy();H=rig.pose.bones[hn].matrix.copy()
  u=(F.translation-U.translation).normalized();v=(H.translation-F.translation).normalized();h=U.to_3x3()@Vector((0,0,-1));target=u.cross(v).normalized()
  h=(h-u*h.dot(u)).normalized();angle=math.atan2(u.dot(h.cross(target)),h.dot(target))
  M=Matrix.Rotation(angle,4,u)@U;M.translation=U.translation;rig.pose.bones[un].matrix=M;bpy.context.view_layer.update()
  rig.pose.bones[fn].matrix=F;bpy.context.view_layer.update();rig.pose.bones[hn].matrix=H;bpy.context.view_layer.update()
  # Open the runner's tightly folded elbows enough to carry a heavy axe clear of the chest.
  bend=u.angle(v);R=Matrix.Rotation(-bend*(.25 if sd=='R'else .10),4,target);M=R@F;M.translation=F.translation;rig.pose.bones[fn].matrix=M;bpy.context.view_layer.update()
 for sd in 'LR':
  for base,child,helper,share in [('Forearm','Hand','ForearmTwist',.5),('UpperArm','Forearm','UpperArmTwist',-.5)]:
   bn=f'B_{sd}_{base}';cn=f'B_{sd}_{child}';b=rig.data.bones[bn];c=rig.data.bones[cn];axis=(b.matrix_local.inverted()@c.head_local).normalized()
   if base=='Forearm':q=(rig.pose.bones[bn].matrix.inverted()@rig.pose.bones[cn].matrix).to_quaternion()@(b.matrix_local.inverted()@c.matrix_local).to_quaternion().inverted()
   else:q=rig.pose.bones[bn].rotation_quaternion
   angle=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);angle=(angle+math.pi)%(2*math.pi)-math.pi
   rig.pose.bones[f'B_{sd}_{helper}'].rotation_quaternion=Quaternion(axis,angle*share)
 bpy.context.view_layer.update()
 frames.append({b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones})
frames[-1]=frames[0]
act(None);bpy.data.actions.remove(bpy.data.actions['Running']);a=bpy.data.actions.new('Running');a.use_fake_user=True;prev={}
worlds=[]
for i,p in enumerate(frames):
 apply(p);worlds.append({b.name:[list(r)for r in rig.matrix_world@b.matrix]for b in rig.pose.bones})
 act(a)
 for n,(q,l)in p.items():
  pb=rig.pose.bones[n]
  if n in prev and q.dot(prev[n])<0:q=-q
  prev[n]=q;pb.rotation_quaternion=q;pb.location=l
  pb.keyframe_insert('rotation_quaternion',frame=i/4);pb.keyframe_insert('location',frame=i/4)
a.use_frame_range=True;a.frame_start=0;a.frame_end=24
for lay in a.layers:
 for strip in lay.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.render.fps=30
(P/'work/round7/running_world.json').write_text(json.dumps({'times':list(np.linspace(0,.8,97)),'poses':worlds,'rest':{b.name:[list(r)for r in rig.matrix_world@b.matrix_local]for b in rig.data.bones}}))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round7/running_author.blend'))
print('STANDARD RUN RETARGET READY')
