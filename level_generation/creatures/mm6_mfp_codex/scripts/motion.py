"""Native relaxed rest and source-derived action adaptation, at the source 30 Hz."""
import bpy,math,json,sys,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_animated.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=30
names=[b.name for b in rig.pose.bones]
def action(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def get():return {b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy())for b in rig.pose.bones}
def put(p):
 action(None)
 for n,(q,l,s)in p.items():
  b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l;b.scale=s
 bpy.context.view_layer.update()
def sample(a,f):
 action(a);sc.frame_set(int(f),subframe=float(f-int(f)));return get()
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def blend(a,b,t):return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t),a[n][2].lerp(b[n][2],t))for n in names}
def wm(n):return rig.pose.bones[n].matrix.copy()
def aim(n,child,direction):
 b=rig.pose.bones[n];m=wm(n);cur=rig.pose.bones[child].head-b.head;q=cur.rotation_difference(direction.normalized());new=q.to_matrix().to_4x4()@m;new.translation=m.translation;b.matrix=new;bpy.context.view_layer.update()
def rotation(n,R):
 m=R.to_4x4();m.translation=rig.pose.bones[n].head;rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
def leg(s,target,R):
 th,ca,ft=[f'B_{s}_'+n for n in ['Thigh','Calf','Foot']];H=rig.pose.bones[th].head.copy();K=rig.pose.bones[ca].head.copy();A=rig.pose.bones[ft].head.copy()
 a=(K-H).length;b=(A-K).length;u=(target-H).normalized();d=min((target-H).length,(a+b)*.9999);v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);E=H+a*(u*c+v*math.sqrt(max(0,1-c*c)))
 aim(th,ca,E-H);aim(ca,ft,target-rig.pose.bones[ca].head);rotation(ft,R)
def anatomical(s):
 U,F,H=[f'B_{s}_'+n for n in ['UpperArm','Forearm','Hand']];u=(rig.pose.bones[F].head-rig.pose.bones[U].head).normalized();f=(rig.pose.bones[H].head-rig.pose.bones[F].head).normalized();ur,fr,hr=[rig.data.bones[n]for n in [U,F,H]]
 hinge=(ur.matrix_local.to_3x3().inverted()@((fr.head_local-ur.head_local).cross(hr.head_local-fr.head_local))).normalized();R=wm(U).to_3x3();h=R@hinge;n=u.cross(f).normalized();ang=math.atan2(h.cross(n).dot(u),h.dot(n));RH=wm(H).to_3x3();rotation(U,Quaternion(u,ang).to_matrix()@R)
 # Anatomical hinge with zero forearm roll; the hand retains the source pronation, spread by twist helpers.
 RF=wm(U).to_3x3()@ur.matrix_local.to_3x3().inverted()@fr.matrix_local.to_3x3();axis=(fr.matrix_local.to_3x3().inverted()@(hr.head_local-fr.head_local)).normalized();RF=(RF@axis).rotation_difference(f).to_matrix()@RF
 rotation(F,RF);rotation(H,RH)
baseline={a.name:[sample(a,f)for f in range(int(a.frame_range[1])+1)]for a in list(bpy.data.actions)}
action(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();foot={}
for s,sign in [('L',1),('R',-1)]:
 ft=f'B_{s}_Foot';T=rig.data.bones[ft].head_local.copy();T.x=sign*.102;T.z+=.002;R=rig.data.bones[ft].matrix_local.to_3x3();leg(s,T,R);foot[s]=(T,R)
 U,F,H=[f'B_{s}_'+n for n in ['UpperArm','Forearm','Hand']]
 aim(U,F,Vector((sign*.12,.04,-1)));aim(F,H,Vector((sign*.13,-.12,-1)));anatomical(s)
 rf=wm(F).to_3x3();rel=rig.data.bones[F].matrix_local.to_3x3().inverted()@rig.data.bones[H].matrix_local.to_3x3();rotation(H,rf@rel)
 for b in rig.pose.bones:
  if b.name.startswith(f'B_{s}_Finger'):b.rotation_quaternion=Quaternion()
 bpy.context.view_layer.update()
rest=get();rest_spine=wm('B_Spine').to_3x3();rest_pelvis=wm('B_Pelvis').to_3x3()
(P/'work/native_rest.json').write_text(json.dumps({n:[list(q),list(l),list(s)]for n,(q,l,s)in rest.items()},indent=2))
common.workbench_clay(sc);common.render_views(str(P/'review/rest_clay'),.825,1.8,views=('front','left','three_quarter'),resolution=(540,810))
def write(name,poses):
 action(None);old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;action(a);prev={}
 for f,p in enumerate(poses):
  for n,(q,l,s)in p.items():
   b=rig.pose.bones[n]
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;b.rotation_quaternion=q;b.location=l;b.scale=s;b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1;action(None)
poses={}
for name in ['Standing','Fidget']:
 out=[]
 for f in range(61):
  put(rest);t=f/60;w=math.sin(t*math.pi)**2
  b=rig.pose.bones['B_Spine2'];b.rotation_quaternion=rest[b.name][0]@Quaternion(Vector((1,0,0)),math.sin(t*math.tau)*math.radians(.18))
  if name=='Fidget':
   for n,angle in [('B_Neck',7),('B_Head',5)]:
    b=rig.pose.bones[n];axis=rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((0,0,1));b.rotation_quaternion=rest[n][0]@Quaternion(axis,math.radians(angle)*w)
   b=rig.pose.bones['B_Pelvis'];b.location=rest[b.name][1]+rig.data.bones[b.name].matrix_local.to_3x3().inverted()@Vector((.003*w,0,0));bpy.context.view_layer.update()
   for sd,(T,R)in foot.items():leg(sd,T,R)
  bpy.context.view_layer.update();out.append(get())
 poses[name]=out
for name in ['Walking','Running','Attack','Hit','Death']:
 out=[];old=baseline[name];nf=len(old)-1
 for f,source in enumerate(old):
  t=f/nf
  if name in ['Walking','Running']:
   p=blend(rest,source,.12);put(p);rotation('B_Pelvis',rest_pelvis);rotation('B_Spine',rest_spine)
   b=rig.pose.bones['B_Pelvis'];b.location=rest[b.name][1]+rig.data.bones[b.name].matrix_local.to_3x3().inverted()@Vector((0,0,-.008*(1-math.cos(t*math.tau*2))))
   bpy.context.view_layer.update()
   for s,sign in [('L',1),('R',-1)]:
    phase=(t+(0 if s=='L' else .5))%1;T,R=foot[s];target=T.copy();duty=.58 if name=='Running' else .60;stride=.19 if name=='Running' else .15
    if phase<duty:target.y+=-stride+2*stride*phase/duty
    else:
     u=(phase-duty)/(1-duty);target.y+=stride-2*stride*smooth(u);target.z+=.105*math.sin(math.pi*u)**1.3
    leg(s,target,R)
    for part in ['Clavicle','UpperArm','Forearm','Hand']:
     n=f'B_{s}_{part}';rig.pose.bones[n].rotation_quaternion=rest[n][0]
    bpy.context.view_layer.update();n=f'B_{s}_UpperArm';rotation(n,Quaternion(Vector((1,0,0)),math.radians(7 if name=='Walking' else 13)*math.sin(t*math.tau)*sign).to_matrix()@wm(n).to_3x3())
    for b in rig.pose.bones:
     if b.name.startswith(f'B_{s}_Finger'):b.rotation_quaternion=Quaternion()
  else:
   lead={'Attack':7,'Hit':3,'Death':7}[name];tail={'Attack':7,'Hit':4,'Death':0}[name];w=smooth(f/lead)*(smooth((nf-f)/tail) if tail else 1);put(blend(rest,source,w))
   if name in ['Attack','Hit']:
    b=rig.pose.bones['B_Pelvis'];b.location=rest[b.name][1].lerp(source[b.name][1],.20*w);bpy.context.view_layer.update()
    for s,(T,R)in foot.items():
     target=T.copy();target.y+=(.022 if s=='R' else -.015)*math.sin(math.pi*t)**2
     target.z+=.015*math.sin(math.pi*min(1,max(0,(t-.2)/.22)))**2 if s=='R' and .2<t<.42 else 0
     leg(s,target,R)
   # Empty hands on impact/death, retaining source arm momentum.
   if name!='Attack':
    for b in rig.pose.bones:
     if 'Finger' in b.name:b.rotation_quaternion=Quaternion()
  bpy.context.view_layer.update()
  for s in 'LR':anatomical(s)
  out.append(get())
 poses[name]=out
poses['Dead']=[poses['Death'][-1]]*31
for name,out in poses.items():write(name,out)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
action(bpy.data.actions['Standing']);sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_motion.blend'))
sys.argv=['grip_from_source.py','--',str(P.parents[2]/'anim_library/humanoid_set/1Hand.glb'),'DaggerAttackR3:12'];runpy.run_path(str(P/'scripts/grip_from_source.py'),run_name='__main__')
import os;os.environ['R_HANDLE']='0.009';os.environ['GRIP_RENDER']=str(P/'review/grip')
sys.argv=['grip_solve.py','--',str(P/'work/rig_motion.blend'),'Attack','15'];runpy.run_path(str(P/'scripts/grip_solve.py'),run_name='__main__')
