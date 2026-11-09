"""Review 2: measured closed carry grip; distinct Cast duplicates the bow shot exactly."""
import bpy,math,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round2/baseline/work/rig_equipped.blend'))
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
# Align the boot sole's measured long axis with travel without changing its floor plane.
yaw_correction={'L':-math.radians(8.09515),'R':math.radians(10.95591)}
for name,frames in baseline.items():
 for i,p in enumerate(frames):
  put(p)
  for side,angle in yaw_correction.items():
   n=f'B_{side}_Foot';rotation(n,Quaternion(Vector((0,0,1)),angle).to_matrix()@wm(n).to_3x3())
  frames[i]=get()
g=Matrix(json.loads((P/'work/round2_bow_binding.json').read_text())['hand_local']);fingers=json.loads((P/'work/grip_pose.json').read_text())['finger_local']
put(baseline['Standing'][0]);h=wm('B_L_Hand');axis=h.to_3x3()@g.to_3x3().col[2]
z=Vector((0,0,1));y=Vector((-.5,-math.sqrt(.75),0));x=y.cross(z);R=Matrix((x,y,z)).transposed()@g.to_3x3().inverted();rotation('B_L_Hand',R);carry=rig.pose.bones['B_L_Hand'].rotation_quaternion.copy()
# Keep the flat-foot rest transforms and the source walk's forward/back timing.
put(baseline['Standing'][0]);footR={s:wm(f'B_{s}_Foot').to_3x3()for s in 'LR'};footT={s:rig.pose.bones[f'B_{s}_Foot'].head.copy()for s in 'LR'}
body=bpy.data.objects['Body'];gn={g.index:g.name for g in body.vertex_groups};sole={s:[v.index for v in body.data.vertices if v.co.z<.009 and sum(g.weight for g in v.groups if gn[g.group]in[f'B_{s}_Foot',f'B_{s}_Toe0'])>.8]for s in 'LR'}
walkz=[]
for p in baseline['Walking']:
 put(p);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();zs={s:min(m.vertices[i].co.z for i in sole[s])for s in 'LR'};ev.to_mesh_clear();walkz.append({s:zs[s]-min(zs.values())for s in 'LR'})
peaks={s:max(z[s]for z in walkz)for s in 'LR'}
poses={}
for name,old in baseline.items():
 if name in ('Cast','Dead'):continue
 out=[];nf=len(old)-1
 for f,p in enumerate(old):
  put(p)
  if name in ('Standing','Fidget','Walking'):q=carry
  else:
   lead={'Attack':12,'Hit':5,'Death':7}[name];tail={'Attack':11,'Hit':6,'Death':0}[name]
   w=smooth(f/lead)*(smooth((nf-f)/tail)if tail else 1);q=carry.slerp(p['B_L_Hand'][0],w)
  rig.pose.bones['B_L_Hand'].rotation_quaternion=q
  if name=='Walking':
   w=math.sin(math.pi*f/nf)**2
   for sd in 'LR':
    ft=f'B_{sd}_Foot';T=rig.pose.bones[ft].head.copy();T.x=footT[sd].x;T.y=footT[sd].y+.64*(T.y-footT[sd].y);T.z=footT[sd].z+.090*walkz[f][sd]/max(peaks[sd],1e-8);leg(sd,T,footR[sd])
   n='B_L_UpperArm';rotation(n,Quaternion(Vector((0,1,0)),math.radians(-5)*w).to_matrix()@wm(n).to_3x3())
   rotation('B_L_Hand',R)

  if name in ('Attack','Hit','Death'):
   # Sweep the long lower limb outside the calf while rotating from the vertical carry.
   lead={'Attack':12,'Hit':5,'Death':7}[name];tail={'Attack':11,'Hit':6,'Death':0}[name]
   envelope=math.sin(math.pi*f/lead)**2 if f<lead else 0.
   if tail and f>nf-tail:envelope=max(envelope,math.sin(math.pi*(nf-f)/tail)**2)
   n='B_L_UpperArm';rotation(n,Quaternion(Vector((0,1,0)),math.radians(-20)*envelope).to_matrix()@wm(n).to_3x3())
  for n,rot in fingers.items():rig.pose.bones[n].rotation_quaternion=Quaternion(rot)
  bpy.context.view_layer.update();rig.pose.bones['Bow'].matrix=wm('B_L_Hand')@g;bpy.context.view_layer.update()
  bm=wm('Bow');neutral=bm@Vector((0,.187,.085));kn=rig.pose.bones['B_R_Finger1'].head.copy();w=smooth((f-20)/6)if name=='Attack'and 21<=f<=36 else 0.;nock=neutral.lerp(kn,w)
  if name=='Attack'and f==37:nock=neutral.lerp(kn,.10)
  m=wm('BowNock');m.translation=nock;rig.pose.bones['BowNock'].matrix=m;bpy.context.view_layer.update()
  target=bm@Vector((0,0,.085));d=(target-nock).normalized();up=bm.to_3x3()@Vector((1,0,0));xx=(up-d*up.dot(d)).normalized();yy=d.cross(xx).normalized();am=Matrix((xx,yy,d)).transposed().to_4x4();am.translation=nock+d*(.32*1.22)
  if name=='Attack'and 12<=f<21:am.translation=kn+d*(.32*1.22)
  rig.pose.bones['Arrow'].matrix=am;rig.pose.bones['Arrow'].scale=p['Arrow'][2];bpy.context.view_layer.update();am.translation=target+d*.08;rig.pose.bones['Socket_Arrow_Release'].matrix=am;bpy.context.view_layer.update();out.append(get())
 poses[name]=out
poses['Cast']=poses['Attack'];poses['Dead']=[poses['Death'][-1]]*31
for name in ['Walking','Attack','Cast','Hit','Death','Fidget']:
 poses[name][0]=poses['Standing'][0]
 if name!='Death':poses[name][-1]=poses['Standing'][-1]
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
(P/'review/round2/floor_corrections.json').write_text(json.dumps(floor_report,indent=2))
action(bpy.data.actions['Standing']);sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
# Sync actions into the active textured object; an orphan mesh named Body is not the textured surface.
import shutil,runpy
shutil.copy2(P/'review/round2/baseline/work/rig_textured.blend',P/'work/rig_textured.blend')
sys.argv=['sync_actions.py','--',str(P/'work/rig_equipped.blend'),str(P/'work/rig_textured.blend')]
runpy.run_path(str(P/'scripts/sync_actions.py'),run_name='__main__')
