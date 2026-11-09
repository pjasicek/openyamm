"""Fit owned-library body motion to Merchant proportions; bake floor IK and anatomical elbows."""
import bpy,json,math,numpy as np,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/actions_geometry_v2.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30
NAMES=[b.name for b in rig.pose.bones]
def act(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def capture():return {b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones}
def apply(p):
 act(None)
 for n,(q,l)in p.items():rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l;rig.pose.bones[n].scale=(1,1,1)
 bpy.context.view_layer.update()
def world(n):return rig.matrix_world@rig.pose.bones[n].matrix
def setworld(n,M):rig.pose.bones[n].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
def sample(a,f):
 act(a);scene.frame_set(int(f),subframe=f%1);return capture()
def smooth(x):x=min(1,max(0,x));return x*x*(3-2*x)
def blend(a,b,t):return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t))for n in a}
def aim(n,child,d):
 M=world(n);u=world(child).translation-M.translation;R=u.normalized().rotation_difference(d.normalized()).to_matrix().to_4x4();t=M.translation.copy();M=R@M;M.translation=t;setworld(n,M)
source=json.loads((P/'work/source_rest.json').read_text());cal={};sole={};flat={};lens={};pv=np.array([a.value for a in body.data.attributes['piece'].data])
for sd in 'LR':
 U,F,H=[rig.data.bones[f'B_{sd}_{n}']for n in ['UpperArm','Forearm','Hand']];u=(F.head_local-U.head_local).normalized();v=(H.head_local-F.head_local).normalized();su=Vector(source[U.name]['seg']).normalized();sh=su.cross(Vector((0,-1,0))).normalized();h=U.matrix_local.to_3x3()@Matrix(source[U.name]['rot']).inverted()@sh
 cal[sd]={'h':U.matrix_local.to_3x3().inverted()@h,'rel':U.matrix_local.to_3x3().inverted()@F.matrix_local.to_3x3(),'v':F.matrix_local.to_3x3().inverted()@v,'u':U.matrix_local.to_3x3().inverted()@u}
 M=rig.data.bones[f'B_{sd}_Foot'].matrix_local
 ids=[v.index for v in body.data.vertices if pv[v.index]==(6 if sd=='L' else 7) and v.co.z<.012]
 sole[sd]=[M.inverted()@body.data.vertices[i].co for i in ids];assert len(ids)>5
 # Align the sole's longitudinal principal axis with travel, retaining its fitted rigid boot frame.
 xy=np.array([tuple(body.data.vertices[i].co)[:2]for i in ids]);axis=np.linalg.eigh(np.cov(xy.T))[1][:,-1]
 if axis[1]>0:axis=-axis
 yaw=math.atan2(axis[0],-axis[1]);flat[sd]=Quaternion((0,0,1),-yaw)@M.to_quaternion()
 H,K,A=[rig.data.bones[f'B_{sd}_{k}'].head_local for k in ['Thigh','Calf','Foot']];lens[sd]=((K-H).length,(A-K).length)
 print('BOOT AXIS',sd,math.degrees(yaw),'sole samples',len(ids))

def solve(sd,T,Q):
 th,ca,ft=[f'B_{sd}_{n}'for n in ['Thigh','Calf','Foot']];H=world(th).translation;a,b=lens[sd];d=(T-H).length
 assert abs(a-b)<d<a+b,('reach',name,f,sd,d,a+b)
 u=(T-H).normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);K=H+a*(u*c+v*math.sqrt(max(0,1-c*c)))
 aim(th,ca,K-H);aim(ca,ft,T-K);M=Q.to_matrix().to_4x4();M.translation=T;setworld(ft,M)
 assert (world(ft).translation-T).length<1e-5

def elbow(sd):
 un,fn,hn=[f'B_{sd}_{n}'for n in ['UpperArm','Forearm','Hand']];U,F,H=[world(n)for n in (un,fn,hn)];u=(F.translation-U.translation).normalized();v=(H.translation-F.translation).normalized();h=(U.to_3x3()@cal[sd]['h']).normalized();off=math.asin(max(-1,min(1,v.dot(h))));flex=math.atan2(h.dot(u.cross(v)),u.dot(v));wanted=max(math.radians(2),min(math.radians(140),flex));nv=Quaternion(h,wanted)@u
 # Preserve the upper arm's transported anatomical plane, never flip its roll to disguise a reversed elbow.
 Rf=U.to_3x3()@cal[sd]['rel'];Rf=(Rf@cal[sd]['v']).rotation_difference(nv).to_matrix()@Rf
 M=Rf.to_4x4();M.translation=F.translation;setworld(fn,M)
 H.translation=world(hn).translation;H=nv.rotation_difference(nv).to_matrix().to_4x4()@H;setworld(hn,H)
 return [math.degrees(flex),math.degrees(off),math.degrees(v.angle(nv))]

def foot_target(sd,phase=None,run=False,step=0,pitch=0):
 lift=0;y=.015
 if phase is not None:
  stance=.49 if run else .56;stride=1.18 if run else .84;travel=stride*stance
  if phase<stance:
   s=phase/stance;y=-travel/2+stride*phase;pitch=-6*(1-smooth(s/.12))+10*smooth((s-.84)/.16)
  else:
   s=(phase-stance)/(1-stance);y=travel/2-travel*smooth(s**1.6);lift=(.115 if run else .085)*math.sin(math.pi*s)**1.25;pitch=10*(1-smooth(s/.25))-6*smooth((s-.78)/.22)
 else:y+=step
 Q=Quaternion((1,0,0),math.radians(pitch))@flat[sd];T=Vector((.166 if sd=='L' else -.166,y,.004+lift-min((Q@v).z for v in sole[sd])))
 return T,Q

roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget'];raw={};worlds={}
for name in roles+['AttackFull']:
 a=bpy.data.actions[name];end=float(a.frame_range[1]);fs=np.arange(0,end+.001,.5);raw[name]=[sample(a,float(f))for f in fs]
 worlds[name]=[]
 for p in raw[name]:
  apply(p);worlds[name].append({n:world(n).copy()for n in ['B_Pelvis','B_L_Foot','B_R_Foot']})
rest=raw['Standing'][0];grip=json.loads((P/'work/grip_pose.json').read_text());report={};final={}
for name in roles:
 frames=[];rows=[]
 if name=='Attack':
  # 0.2 s to draw the club, followed by the original slash and a 0.25 s return.
  count=len(raw[name])+27
 else:count=len(raw[name])
 for i in range(count):
  f=i*.5;t=f/30
  if name=='Attack':
   j=max(0,min(len(raw[name])-1,i-12));p=raw[name][j];p=blend(rest,p,smooth(i/12)*smooth((count-1-i)/15))
  else:p=raw[name][i]
  if name in ['Walking','Running']:
   p={n:((rest[n][0].slerp(q,.25 if name=='Walking' else .45) if any(k in n for k in ['Clavicle','UpperArm','Forearm','Hand','Finger'])else q),l)for n,(q,l)in p.items()}
  if name=='Fidget':p=blend(rest,p,.18)
  if name=='Attack':
   p={n:((rest[n][0].slerp(q,.72)if n.startswith('B_Spine')else q),l)for n,(q,l)in p.items()}
  if name=='Hit':
   p={n:((q@raw[name][0][n][0].inverted())@rest[n][0],l-raw[name][0][n][1]+rest[n][1])for n,(q,l)in p.items()}
  apply(p)
  if name!='Death':
   pel=world('B_Pelvis');pel.translation=Vector((0,0,.937 if name not in ['Walking','Running']else(.88 if name=='Running'else .952)))
   if name=='Attack':pel.translation.z-=min(.03,abs(worlds['AttackFull'][j]['B_Pelvis'].translation.z-worlds['AttackFull'][0]['B_Pelvis'].translation.z)*.2)
   targets={}
   for sd in 'LR':
    if name in ['Walking','Running']:T,Q=foot_target(sd,(f/24+.28+(0 if sd=='L'else .5))%1,name=='Running')
    else:
     step=0
     if name=='Attack':
      phase=j/(len(raw[name])-1);dy=(worlds['AttackFull'][j][f'B_{sd}_Foot'].translation-worlds['AttackFull'][0][f'B_{sd}_Foot'].translation).y*.2;step=max(-.075,min(.075,dy));window=(.12,.42)if sd=='R'else(.55,.86);w=smooth((phase-window[0])/.07)*smooth((window[1]-phase)/.07);T,Q=foot_target(sd,step=step*w);T.z+=.035*math.sin(math.pi*min(1,max(0,(phase-window[0])/(window[1]-window[0]))))**2
     else:T,Q=foot_target(sd)
    targets[sd]=(T,Q)
   setworld('B_Pelvis',pel)
   for sd,(T,Q)in targets.items():
    H=world(f'B_{sd}_Thigh').translation;a,b=lens[sd];reach=a+b-.003;planar=(T.x-H.x)**2+(T.y-H.y)**2;pel.translation.z=min(pel.translation.z,T.z+math.sqrt(reach*reach-planar)+pel.translation.z-H.z)
   setworld('B_Pelvis',pel)
   for sd,(T,Q)in targets.items():solve(sd,T,Q)
  for sd in 'LR':
   # A relaxed stocky body needs the native arm clearance; rotate the library chain at the shoulder.
   n=f'B_{sd}_UpperArm';M=world(n);h=M.translation.copy();angle=math.radians(-11 if sd=='L'else 11)
   if name in ['Hit','Attack']:angle*=1.28
   if name=='Death':angle*=.9
   M=Matrix.Rotation(angle,4,'Y')@M;M.translation=h;setworld(n,M)
   rows.append(elbow(sd))
  # Unarmed native poses keep softly bent fingers; close only for the drawn club.
  w=smooth(i/12)*smooth((count-1-i)/15)if name=='Attack'else 0
  for n in NAMES:
   if 'Finger'in n:
    q=rest[n][0]
    if n.startswith('B_R_')and n in grip['finger_local']:q=q.slerp(Quaternion(grip['finger_local'][n]),w)
    rig.pose.bones[n].rotation_quaternion=q
  bpy.context.view_layer.update();frames.append(capture())
 final[name]=frames;report[name]={'samples':count,'source_flex_range_deg':[min(x[0]for x in rows),max(x[0]for x in rows)],'max_elbow_direction_correction_deg':max(x[2]for x in rows)};print('FITTED',name,report[name],flush=True)
final['Dead']=[final['Death'][-1]]*61
act(None)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for name,frames in final.items():
 a=bpy.data.actions.new(name);a.use_fake_user=True;prev={};act(a)
 for i,p in enumerate(frames):
  for n,(q,l)in p.items():
   pb=rig.pose.bones[n]
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=i*.5)
   if n=='B_Pelvis'or any(k in n for k in ['Thigh','Calf','Foot']):pb.keyframe_insert('location',frame=i*.5)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=(len(frames)-1)*.5
 for lay in a.layers:
  for strip in lay.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/'review/motion_fit.json').write_text(json.dumps(report,indent=2));act(bpy.data.actions['Standing']);scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_v1.blend'))
import common
common.workbench_clay(scene)
for name in roles:
 a=bpy.data.actions[name];act(a)
 for i in range(5):
  f=a.frame_range[1]*i/4;scene.frame_set(int(f),subframe=f%1);lo,hi=common.world_bounds([body]);mid=(lo+hi)*.5;common.render_views(str(P/'review'/f'motion_v1_{name}_{i}'),mid.z,max(2.05,(hi-lo).length*.9),target=(mid.x,mid.y),views=('front','left','three_quarter'),resolution=(300,450))
