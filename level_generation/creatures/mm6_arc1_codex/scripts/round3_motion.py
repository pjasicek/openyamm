"""Move the accepted closed carry grip next to the thigh; preserve all R2 geometry."""
import bpy,math,json,sys,runpy
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round3/baseline/work/rig_equipped.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=30;names=[b.name for b in rig.pose.bones]
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


baseline={a.name:[sample(a,f)for f in range(int(a.frame_range[1])+1)]for a in list(bpy.data.actions)}
put(baseline['Standing'][0]);old=get()
U,F,H=['B_L_'+n for n in ['UpperArm','Forearm','Hand']]
S=rig.pose.bones[U].head.copy();E=rig.pose.bones[F].head.copy();W=rig.pose.bones[H].head.copy();R=wm(H).to_3x3()
a=(E-S).length;b=(W-E).length;T=Vector((.180,-.110,.914));u=(T-S).normalized();d=min((T-S).length,(a+b)*.997);T=S+u*d
v=Vector((0,1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);K=S+a*(u*c+v*math.sqrt(max(0,1-c*c)))
aim(U,F,K-S);aim(F,H,T-rig.pose.bones[F].head);rotation(H,R);anatomical('L');new=get()
delta={n:new[n][0]@old[n][0].inverted()for n in [U,F]};poses={}
for name,frames in baseline.items():
 if name=='Cast':continue
 out=[];nf=len(frames)-1
 for f,p in enumerate(frames):
  put(p);RH=wm(H).to_3x3();before=wm(H);props={n:before.inverted()@wm(n)for n in ['Bow','BowNock','Arrow','Socket_Arrow_Release']}
  if name in ['Standing','Fidget','Walking']:weight=1.
  elif name=='Dead':weight=0.
  else:
   lead={'Attack':12,'Hit':5,'Death':7}[name];tail={'Attack':11,'Hit':3,'Death':0}[name]
   weight=1-smooth(f/lead)*(smooth((nf-f)/tail)if tail else 1)
  for n in [U,F]:rig.pose.bones[n].rotation_quaternion=Quaternion().slerp(delta[n],weight)@p[n][0]
  bpy.context.view_layer.update()
  if name=='Walking':rotation(U,Quaternion(Vector((0,1,0)),math.radians(-15)*math.sin(math.pi*f/nf)).to_matrix()@wm(U).to_3x3())
  rotation(H,Quaternion(Vector((0,0,1)),-math.pi/2*weight).to_matrix()@RH)
  for n,m in props.items():rig.pose.bones[n].matrix=wm(H)@m;bpy.context.view_layer.update()
  rig.pose.bones['Arrow'].scale=p['Arrow'][2];out.append(get())
 poses[name]=out
poses['Cast']=poses['Attack']
for name,out in poses.items():write(name,out)
FA,UA=.6,.5
code=(P/'scripts/twist_bones.py').read_text();exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')])
for a in list(bpy.data.actions):bake_twist(a)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     prev=None
     for k in fc.keyframe_points:k.interpolation='LINEAR'
action(bpy.data.actions['Standing']);sc.frame_set(0)
print('NEW_POSITIONS',json.dumps({n:list(rig.pose.bones[n].head)for n in [U,F,H,'Bow','B_L_Thigh']}))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
for dst in [P/'work/rig_textured.blend']+[P/f'work/round2/lod{i}.blend'for i in range(4)]:
 sys.argv=['sync_actions.py','--',str(P/'work/rig_equipped.blend'),str(dst)];runpy.run_path(str(P/'scripts/sync_actions.py'),run_name='__main__')
sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured.blend'));rig=bpy.data.objects['Rig'];action(bpy.data.actions['Standing']);bpy.context.scene.frame_set(0)
common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(P/'review/round3/after'),.85,1.85,views=('front','left','three_quarter'),resolution=(700,1000))
