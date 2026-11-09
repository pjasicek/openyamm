"""Review 1: native upright rest, flat planted soles and rest-relative clip transitions."""
import bpy,math,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round1/baseline/work/rig_equipped.blend'))
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
 hinge=(ur.matrix_local.to_3x3().inverted()@((fr.head_local-ur.head_local).cross(hr.head_local-fr.head_local))).normalized();R=wm(U).to_3x3();h=R@hinge;n=u.cross(f).normalized();ang=math.atan2(h.cross(n).dot(u),h.dot(n));RF=wm(F).to_3x3();RH=wm(H).to_3x3();rotation(U,Quaternion(u,ang).to_matrix()@R);rotation(F,RF);rotation(H,RH)
# Preserve complete baseline poses, including equipment translation and visibility channels.
baseline={a.name:[sample(a,f)for f in range(int(a.frame_range[1])+1)]for a in list(bpy.data.actions)}
action(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
# Native front: feet approximately 23/256 of total height apart, arms within 6 degrees of vertical.
foot={}
for s,sign in [('L',1),('R',-1)]:
 ft=f'B_{s}_Foot';T=rig.data.bones[ft].head_local.copy();T.x-=sign*.125;T.z+=.0015;R=rig.data.bones[ft].matrix_local.to_3x3();leg(s,T,R);foot[s]=(T,R)
 U,F,H=[f'B_{s}_'+n for n in ['UpperArm','Forearm','Hand']]
 aim(U,F,Vector((sign*.075,.06,-1)));aim(F,H,Vector((sign*.17,-.10,-1)));anatomical(s)
 # Relaxed fingers and a neutral wrist follow the forearm's minimally swung source frame.
 rf=wm(F).to_3x3();rel=rig.data.bones[F].matrix_local.to_3x3().inverted()@rig.data.bones[H].matrix_local.to_3x3();rotation(H,rf@rel)
 for b in rig.pose.bones:
  if b.name.startswith(f'B_{s}_Finger'):b.rotation_quaternion=Quaternion()
 bpy.context.view_layer.update()
# A loose side carry: the longbow runs beside the leg; its string faces the body.
h=wm('B_L_Hand');z=Vector((.06,0,1)).normalized();y=Vector((0,1,0));x=y.cross(z);bm=Matrix((x,y,z)).transposed().to_4x4();bm.translation=h.translation+Vector((.027,-.035,-.050));rig.pose.bones['Bow'].matrix=bm
rig.pose.bones['Arrow'].scale=(.001,)*3
bpy.context.view_layer.update();rest=get();put(rest);rest_spine=wm('B_Spine').to_3x3();rest_bow=wm('Bow').to_3x3();rest_bow_offset=wm('Bow').translation-wm('B_L_Hand').translation
(P/'work/round1_rest.json').write_text(json.dumps({n:[list(q),list(l),list(s)]for n,(q,l,s)in rest.items()},indent=2))
common.workbench_clay(sc)
common.render_views(str(P/'review/round1/rest_clay'),.87,1.95,views=('front','left','three_quarter'),resolution=(650,900))
# Save the diagnostic pose before authoring the complete clip set.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_rest.blend'))

def write(name,poses):
 action(None);old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;action(a);prev={}
 for f,p in enumerate(poses):
  for n,(q,l,s)in p.items():
   b=rig.pose.bones[n]
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;b.rotation_quaternion=q;b.location=l;b.scale=s
   b.keyframe_insert('rotation_quaternion',frame=f)
   if n in ('B_Pelvis','Bow','BowNock','Arrow','Socket_Arrow_Release'):b.keyframe_insert('location',frame=f)
   if n=='Arrow':b.keyframe_insert('scale',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1;action(None)
 return a
poses={}
for name,nf in [('Standing',60),('Fidget',60)]:
 out=[]
 for f in range(nf+1):
  put(rest);t=f/nf;breath=math.sin(t*math.tau)*math.radians(.18)
  b=rig.pose.bones['B_Spine2'];b.rotation_quaternion=rest[b.name][0]@Quaternion(Vector((1,0,0)),breath)
  if name=='Fidget':
   w=math.sin(math.pi*t)**2
   for n,angle in [('B_Neck',7),('B_Head',5)]:
    b=rig.pose.bones[n];axis=rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((0,0,1));b.rotation_quaternion=rest[n][0]@Quaternion(axis,math.radians(angle)*w)
   b=rig.pose.bones['B_Pelvis'];b.location=rest[b.name][1]+rig.data.bones[b.name].matrix_local.to_3x3().inverted()@Vector((.004*w,0,0));bpy.context.view_layer.update()
   for sd,(T,R)in foot.items():leg(sd,T,R)
  bpy.context.view_layer.update();out.append(get())
 poses[name]=out
# The stride retains its source foot travel and timing; its boundary blends and relaxed arm carry meet the new idle.
for name in ['Walking','Attack','Cast','Hit','Death']:
 out=[];old=baseline[name];nf=len(old)-1
 for f,p in enumerate(old):
  if name=='Walking':
   p={n:tuple(x.copy()for x in v)for n,v in p.items()}
   for n in names:
    if any(n.startswith(f'B_{sd}_'+part)for sd in 'LR'for part in ['Clavicle','UpperArm','Forearm','Hand','Finger'])or n in ['Bow','BowNock','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:p[n]=rest[n]
   lead=3;tail=3
  else:lead={'Attack':12,'Cast':12,'Hit':5,'Death':7}[name];tail={'Attack':11,'Cast':9,'Hit':6,'Death':0}[name]
  w=smooth(f/lead)
  if tail:w*=smooth((nf-f)/tail)
  p=blend(rest,p,w);put(p)
  if name=='Walking':
   rotation('B_Spine',rest_spine)
   n='B_L_UpperArm';rotation(n,Quaternion(Vector((0,1,0)),math.radians(-2)*w).to_matrix()@wm(n).to_3x3())
   # A small relaxed free-arm swing; the bow hand stays beside the leg.
   n='B_R_UpperArm';b=rig.pose.bones[n];axis=rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0));b.rotation_quaternion=p[n][0]@Quaternion(axis,math.radians(5)*math.sin(f/nf*math.tau)*w)
   bpy.context.view_layer.update()
   # Keep the loose bow upright beside the leg as the gait turns the pelvis.
   bm=rest_bow.to_4x4();bm.translation=wm('B_L_Hand').translation+rest_bow_offset;rig.pose.bones['Bow'].matrix=bm;bpy.context.view_layer.update()
  if name=='Attack' and 0<f<12:
   n='B_L_UpperArm';R=Quaternion(Vector((0,1,0)),math.radians(-7)*math.sin(math.pi*f/12)).to_matrix()@wm(n).to_3x3();rotation(n,R)
   rotation('Bow',Quaternion(Vector((0,1,0)),math.radians(2)*math.sin(math.pi*f/12)).to_matrix()@wm('Bow').to_3x3())
  if name=='Hit':rotation('B_Neck',Quaternion(Vector((1,0,0)),math.radians(14)*math.sin(math.pi*f/nf)**2).to_matrix()@wm('B_Neck').to_3x3())
  out.append(get())
 poses[name]=out
poses['Dead']=[poses['Death'][-1]]*31
for name,out in poses.items():write(name,out)
# Motion edits are rotations only on anatomical joints; rebuild the existing deformation twist helpers.
FA,UA=.6,.5
code=(P/'scripts/twist_bones.py').read_text();exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')])
for a in list(bpy.data.actions):bake_twist(a)
# Linear keys, continuous quaternion signs, and conservative subframe floor clearance on transitional clips.
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
root=rig.pose.bones['B_Pelvis'];inv=rig.data.bones[root.name].matrix_local.to_3x3().inverted();floor_report={}
for a in bpy.data.actions:
 action(a);nf=int(a.frame_range[1]);loc=[];corr=[0.]*(nf+1)
 for f in range(nf+1):sc.frame_set(f);loc.append(root.location.copy())
 for tick in range(nf*4+1):
  f=tick/4;sc.frame_set(int(f),subframe=f-int(f));lo,_=common.world_bounds([bpy.data.objects['Body'],bpy.data.objects['BowAsset']]);dz=max(0.,.00035-lo.z)
  for j in {int(f),min(nf,math.ceil(f))}:corr[j]=max(corr[j],dz)
 for f,l in enumerate(loc):root.location=l+inv@Vector((0,0,corr[f]));root.keyframe_insert('location',frame=f)
 floor_report[a.name]={'max_root_floor_correction_m':max(corr)}
(P/'review/round1/floor_corrections.json').write_text(json.dumps(floor_report,indent=2))
action(bpy.data.actions['Standing']);sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
# Reuse the approved textured mesh without changing its UVs or textures; only replace its action datablocks.
with bpy.data.libraries.load(str(P/'review/round1/baseline/work/rig_textured.blend'),link=False)as(src,dst):dst.meshes=['Body']
body=bpy.data.objects['Body'];body.data=dst.meshes[0]
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_textured.blend'))
print('ROUND1_CLIPS',floor_report)
