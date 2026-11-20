"""Review 5: native upward bow/string, forward fist, and planted Attack/Cast soles."""
import bpy,math,json,sys,runpy
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round4/baseline/work/rig_equipped.blend'))
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
def balance_carry_roll():
 # Rotate the forearm around its length while holding the hand/prop world frame fixed.
 F,H='B_L_Forearm','B_L_Hand';fr=rig.data.bones[F].matrix_local.to_3x3();hr=rig.data.bones[H].matrix_local.to_3x3()
 axis=hr.inverted()@(sum((rig.data.bones[f'B_L_Finger{i}'].head_local for i in range(5)),Vector())/5-rig.data.bones[H].head_local).normalized()
 RF,RH=wm(F).to_3x3(),wm(H).to_3x3();world_axis=(rig.pose.bones[H].head-rig.pose.bones[F].head).normalized()
 def roll(R):
  q=((R@fr.inverted()@hr).inverted()@RH).to_quaternion();t=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)
  return (t+math.pi)%(2*math.pi)-math.pi
 angle=roll(RF);limit=math.radians(35)
 if abs(angle)>limit:
  probe=Quaternion(world_axis,.001).to_matrix()@RF;derivative=(roll(probe)-angle)/.001
  correction=(math.copysign(limit,angle)-angle)/derivative
  rotation(F,Quaternion(world_axis,correction).to_matrix()@RF);rotation(H,RH)
  assert abs(roll(wm(F).to_3x3()))<math.radians(36)
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
U,F,H=['B_L_'+n for n in ['UpperArm','Forearm','Hand']];mirror=Matrix.Diagonal((-1,1,1));prop_names=['Bow','BowNock','Arrow','Socket_Arrow_Release'];direction=Vector((0,-math.cos(math.radians(18)),math.sin(math.radians(18))))
def mirrored(part):
 L='B_L_'+part;R='B_R_'+part
 return mirror@wm(R).to_3x3()@rig.data.bones[R].matrix_local.to_3x3().inverted()@mirror@rig.data.bones[L].matrix_local.to_3x3()
def rest():
 original={n:wm(n)for n in prop_names};bind=wm(H).inverted()@original['Bow']
 target={p:mirrored(p)for p in ['UpperArm','Forearm','Hand']}
 for part in ['UpperArm','Forearm']:rotation('B_L_'+part,target[part])
 # Keep the accepted front silhouette; native side view puts the closed fist just forward of the hip.
 # Solve the native forward wrist offset with a modest elbow bend; retain the front lateral position.
 shoulder=rig.pose.bones[U].head.copy();elbow=rig.pose.bones[F].head.copy();wrist=rig.pose.bones[H].head.copy()
 a=(elbow-shoulder).length;b=(wrist-elbow).length;hip=rig.pose.bones['B_L_Thigh'].head
 end=Vector((wrist.x,hip.y-.05859375*1.6989782874,wrist.z))
 reach=math.sqrt(a*a+b*b+2*a*b*math.cos(math.radians(25)))
 end.z=shoulder.z-math.sqrt(reach*reach-(end.x-shoulder.x)**2-(end.y-shoulder.y)**2)
 u=(end-shoulder).normalized();d=(end-shoulder).length
 pole=Vector((0,1,0));pole=(pole-u*pole.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d)
 bend=shoulder+a*(u*c+pole*math.sqrt(max(0,1-c*c)))
 aim(U,F,bend-shoulder);aim(F,H,end-rig.pose.bones[F].head)
 anatomical('L')
 raw=target['Hand']@bind.to_3x3();q=raw.col[2].normalized().rotation_difference(direction);rotation(H,q.to_matrix()@target['Hand'])
 M=wm(H)@bind
 poses={'Bow':M,**{n:M@original['Bow'].inverted()@original[n]for n in prop_names if n!='Bow'}}
 for n in prop_names:rig.pose.bones[n].matrix=poses[n];bpy.context.view_layer.update()
 return get()
put(baseline['Standing'][0]);old=get();oldH=wm(H).to_3x3();target=rest();newH=wm(H).to_3x3();delta={n:target[n][0]@old[n][0].inverted()for n in [U,F]};hand_delta=newH@oldH.inverted();poses={};carry_bind=wm(H).inverted()@wm('Bow');carry_children={n:wm('Bow').inverted()@wm(n)for n in prop_names if n!='Bow'}
for name,frames in baseline.items():
 if name=='Cast':continue
 out=[];nf=len(frames)-1
 for f,p in enumerate(frames):
  put(p)
  if name in ['Standing','Fidget','Walking']:out.append(rest());continue
  if name=='Hit':
   # Carry the bow outward through the library recoil, with a smooth return and a steady grip frame.
   for n in [U,F,H]:rig.pose.bones[n].rotation_quaternion=target[n][0]
   bpy.context.view_layer.update()
   theta=math.radians(20)*math.sin(math.pi*f/nf)**2
   rotation(U,Quaternion(Vector((0,1,0)),-theta).to_matrix()@wm(U).to_3x3())
   rotation(H,newH);balance_carry_roll()
   M=wm(H)@carry_bind
   carried={'Bow':M,**{n:M@carry_children[n]for n in carry_children}}
   for n in prop_names:rig.pose.bones[n].matrix=carried[n];bpy.context.view_layer.update()
   rig.pose.bones['Arrow'].scale=p['Arrow'][2];out.append(get());continue
  if name=='Dead':out.append(get());continue
  lead={'Attack':12,'Hit':5,'Death':7}[name];tail={'Attack':11,'Hit':6,'Death':0}[name];w=1-smooth(f/lead)*(smooth((nf-f)/tail)if tail else 1)
  orig={n:wm(n)for n in prop_names};old_hand=wm(H);bind=old_hand.inverted()@orig['Bow']
  for n in [U,F]:rig.pose.bones[n].rotation_quaternion=Quaternion().slerp(delta[n],w)@p[n][0]
  bpy.context.view_layer.update();rotation(H,Quaternion().slerp(hand_delta.to_quaternion(),w).to_matrix()@old_hand.to_3x3())
  M=wm(H)@bind;prop_poses={'Bow':M,**{n:M@orig['Bow'].inverted()@orig[n]for n in prop_names if n!='Bow'}}
  for n in prop_names:rig.pose.bones[n].matrix=prop_poses[n];bpy.context.view_layer.update()
  rig.pose.bones['Arrow'].scale=p['Arrow'][2];out.append(get())
 poses[name]=out
# Both shooting feet use the accepted flat Standing ankle/toe frames throughout the clip.
put(poses['Standing'][0]);footR={s:wm(f'B_{s}_Foot').to_3x3() for s in 'LR'}
footT={s:rig.pose.bones[f'B_{s}_Foot'].head.copy() for s in 'LR'}
for i,p in enumerate(poses['Attack']):
 put(p)
 # Keep both fixed anchors reachable during the source pelvis sway instead of lifting an ankle.
 drop=0.
 for side in 'LR':
  th,ca,ft=[rig.pose.bones[f'B_{side}_'+n].head.copy()for n in ['Thigh','Calf','Foot']]
  reach=(ca-th).length+(ft-ca).length-.0001;delta=th-footT[side]
  limit=footT[side].z+math.sqrt(max(0,reach*reach-delta.x*delta.x-delta.y*delta.y))
  drop=max(drop,th.z-limit)
 if drop>0:
  pelvis=rig.pose.bones['B_Pelvis'];m=wm('B_Pelvis');m.translation.z-=drop;pelvis.matrix=m;bpy.context.view_layer.update()
 for side in 'LR':
  leg(side,footT[side],footR[side])
  rig.pose.bones[f'B_{side}_Toe0'].rotation_quaternion=poses['Standing'][0][f'B_{side}_Toe0'][0]
 bpy.context.view_layer.update();poses['Attack'][i]=get()
poses['Attack'][0]=poses['Standing'][0];poses['Attack'][-1]=poses['Standing'][-1]
# A hidden nocked arrow uses actual zero scale; .001 leaves a tiny solid inside the carried body.
for frames in poses.values():
 for pose in frames:
  if max(abs(x)for x in pose['Arrow'][2])<.002:pose['Arrow']=(pose['Arrow'][0],pose['Arrow'][1],Vector((0,0,0)))
poses['Cast']=poses['Attack']
for name,frames in poses.items():write(name,frames)
FA,UA=.6,.5
code=(P/'scripts/twist_bones.py').read_text().replace('twist_about(dq, seg_local) * FA', 'twist_about(dq, seg_local) * (.4 if act.name == "Hit" and s == "L" and f0 < f < f1 else FA)');exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')])
for a in list(bpy.data.actions):bake_twist(a)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
action(bpy.data.actions['Standing']);sc.frame_set(0)
report={n:{'head':list(rig.pose.bones[n].head),'matrix':[list(row)for row in wm(n)]}for n in [U,F,H,'B_R_Hand','Bow','BowNock']};(P/'review/round5/pose_intent.json').write_text(json.dumps(report,indent=2))
assert wm('Bow').to_3x3().col[2].normalized().dot(direction)>.99999
assert wm('Bow').to_3x3().col[1].z>.8
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
for dst in [P/'work/rig_textured.blend']+[P/f'work/round2/lod{i}.blend'for i in range(4)]:
 sys.argv=['sync_actions.py','--',str(P/'work/rig_equipped.blend'),str(dst)];runpy.run_path(str(P/'scripts/sync_actions.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round3_export.py'),run_name='__main__')
