"""Round 3: upright carry, palm-in free arm, forward flat feet; Cast is the library bow shot."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_round2.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
def action(a):
 rig.animation_data.action=a
 if a is not None:rig.animation_data.action_slot=a.slots[0]
def get():return {b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy()) for b in rig.pose.bones}
def put(p):
 action(None)
 for n,(q,l,s) in p.items():b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=s
 bpy.context.view_layer.update()
def sample(a,f):
 action(a);sc.frame_set(int(f),subframe=float(f%1));return get()
def rot(n,R):
 b=rig.pose.bones[n];m=R.to_4x4();m.translation=b.head;b.matrix=m;bpy.context.view_layer.update()
def aim(n,c,v):
 b=rig.pose.bones[n];rot(n,(rig.pose.bones[c].head-b.head).rotation_difference(v).to_matrix()@b.matrix.to_3x3())
def ik(names,T,pole):
 U,F,H=names;u,f,h=[rig.pose.bones[n] for n in names];A=u.head.copy();a=(f.head-A).length;b=(h.head-f.head).length
 d=min((T-A).length,(a+b)*.999);v=(T-A).normalized();p=(pole-v*pole.dot(v)).normalized();c=np.clip((a*a+d*d-b*b)/(2*a*d),-1,1)
 E=A+a*(v*c+p*math.sqrt(1-c*c));aim(U,F,E-A);aim(F,H,T-rig.pose.bones[F].head)
def ease(x):x=np.clip(x,0,1);return float(x*x*(3-2*x))
def anatomy(s):
 U,F,H=[f'B_{s}_{n}'for n in ['UpperArm','Forearm','Hand']];u=(rig.pose.bones[F].head-rig.pose.bones[U].head).normalized();v=(rig.pose.bones[H].head-rig.pose.bones[F].head).normalized();normal=u.cross(v).normalized()
 for n,axis in [(U,u),(F,v)]:
  keepF=rig.pose.bones[F].matrix.copy();keepH=rig.pose.bones[H].matrix.copy();m=rig.pose.bones[n].matrix;old=-m.to_3x3().col[2].normalized();old=(old-axis*old.dot(axis)).normalized();angle=math.atan2(axis.dot(old.cross(normal)),old.dot(normal));rot(n,Quaternion(axis,angle).to_matrix()@m.to_3x3())
  if n==U:rig.pose.bones[F].matrix=keepF;bpy.context.view_layer.update()
  rig.pose.bones[H].matrix=keepH;bpy.context.view_layer.update()
def frame(f,n):
 f=f.normalized();n=(n-f*n.dot(f)).normalized();return Matrix((f.cross(n),f,n)).transposed()
baseline={a.name:[sample(a,f)for f in range(int(a.frame_range[1])+1)]for a in list(bpy.data.actions)}
put(baseline['Standing'][0]);homefeet={s:rig.pose.bones[f'B_{s}_Foot'].head.copy()for s in 'LR'}
action(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
coords=np.array([tuple(v.co)for v in body.data.vertices]);pv=np.array([x.value for x in body.data.attributes['piece'].data]);gn={g.index:g.name for g in body.vertex_groups}
feet={};report={'feet':{},'cast_choice':'b: exact Attack copy, Socket_Arrow','carry_bow_tilt_degrees':20}
for s in 'LR':
 ft=rig.data.bones[f'B_{s}_Foot'];R=ft.matrix_local.to_3x3();H=ft.head_local
 ids=[v.index for v in body.data.vertices if v.co.z<.13 and sum(g.weight for g in v.groups if gn[g.group]in[f'B_{s}_Foot',f'B_{s}_Toe0'])>.55]
 pts=coords[ids];front=pts[pts[:,1]<np.percentile(pts[:,1],20)].mean(0);forward=Vector(front)-H;forward.z=0;forward.normalize()
 yaw=math.atan2(forward.x,-forward.y);Q=Matrix.Rotation(-yaw,3,'Z');Rf=Q@R
 rel=np.array([tuple(Q@(Vector(v)-H))for v in pts]);height=-float(rel[:,2].min())+.0008
 feet[s]={'ids':ids,'R':Rf,'height':height,'forward_local':R.inverted()@forward}
 report['feet'][s]={'rest_mesh_forward':list(forward),'yaw_correction_deg':math.degrees(-yaw),'sole_ankle_height':height,'forward_foot_local':list(feet[s]['forward_local'])}
# Palm sign was measured from fitted finger flexion in round 2.
normal=Vector(json.loads((P/'work/cast_intent.json').read_text())['palm_normal_hand_local'])
hr=rig.data.bones['B_R_Hand'];fwd=hr.matrix_local.inverted()@rig.data.bones['B_R_Finger2'].head_local
palmframe=frame(fwd,normal)
g=rig.data.bones['B_L_Hand'].matrix_local.inverted()@rig.data.bones['Bow'].matrix_local
carryR=Matrix.Rotation(math.radians(-30),3,'Z')@Matrix.Rotation(math.radians(20),3,'X');handR=carryR@g.to_3x3().inverted()
restprop={n:rig.data.bones[n].matrix_local.copy()for n in ['Arrow','StringTop','StringBottom']}
# Source sole clearance supplies the gait phase; the edited feet retain real steps, not toe-out rotation.
gait={}
for role in ['Walking','Running']:
 rows=[]
 for pose in baseline[role]:
  put(pose);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z={s:min(me.vertices[i].co.z for i in feet[s]['ids'])for s in 'LR'};ev.to_mesh_clear();rows.append({s:max(0,z[s]-min(z.values()))for s in 'LR'})
 peaks={s:max(r[s]for r in rows)for s in 'LR'};gait[role]=[{s:r[s]/max(peaks[s],1e-6)for s in 'LR'}for r in rows]
anchors={}
for f in [19,23]:
 put(baseline['Attack'][f]);anchors[f]={'hand':rig.pose.bones['B_L_Hand'].matrix.copy(),'pole':rig.pose.bones['B_L_Forearm'].head-(rig.pose.bones['B_L_UpperArm'].head+rig.pose.bones['B_L_Hand'].head)*.5}
for anchor in anchors.values():
 h=anchor['hand'];R=(h@g).to_3x3()@Matrix.Rotation(math.radians(-75),3,'Z')@g.to_3x3().inverted();hrot=R.to_4x4();hrot.translation=h.translation;anchor['hand']=hrot
poses={};intent={} 
for role,old in baseline.items():
 if role in ['Cast','Dead']:continue
 out=[];N=len(old)-1;intents=[]
 for f,p in enumerate(old):
  put(p);oldpose=get()
  free=role in ['Standing','Fidget','Walking','Running','Hit'];w=1.
  if role=='Attack':w=1-ease(f/12) if f<=12 else ease((f-27)/6)
  if role=='Death':w=1-ease(f/4)
  oldH={s:rig.pose.bones[f'B_{s}_Hand'].matrix.copy()for s in 'LR'}
  if w>0:
   swing=math.sin(math.tau*f/N) if role in ['Walking','Running']else 0
   U='B_R_UpperArm';shoulder=rig.pose.bones[U].head.copy()
   T=Vector((-.34,.01+.045*swing,shoulder.z-.43));ik([U,'B_R_Forearm','B_R_Hand'],T,Vector((-1,-.25,0)))
   fore=(rig.pose.bones['B_R_Hand'].head-rig.pose.bones['B_R_Forearm'].head).normalized()
   rot('B_R_Hand',frame(fore,Vector((1,0,0)))@palmframe.inverted())
   shoulder=rig.pose.bones['B_L_UpperArm'].head.copy();T=Vector((.45,-.28,shoulder.z-.32))
   if role=='Hit':T=Vector((.45,-.28-.025*math.sin(math.pi*f/N)**2,shoulder.z-.32))
   ik(['B_L_UpperArm','B_L_Forearm','B_L_Hand'],T,Vector((1,2,0)));rot('B_L_Hand',handR)
   rig.pose.bones['Bow'].rotation_quaternion=Quaternion();rig.pose.bones['Bow'].location=Vector()
   bpy.context.view_layer.update()
   target=get();targetH={sd:rig.pose.bones[f'B_{sd}_Hand'].matrix.copy()for sd in 'LR'}
   if w<1:
    for n in target:
     if any(n.startswith(f'B_{s}_{k}')for s in 'LR'for k in ['UpperArm','Forearm','Hand'])or n=='Bow':
      q,l,scale=oldpose[n];rig.pose.bones[n].rotation_quaternion=q.slerp(target[n][0],w);rig.pose.bones[n].location=l.lerp(target[n][1],w)
    bpy.context.view_layer.update()
    for sd,sign in [('L',1),('R',-1)]:
     T=oldH[sd].translation.lerp(targetH[sd].translation,w);R=oldH[sd].to_quaternion().slerp(targetH[sd].to_quaternion(),w).to_matrix()
     ik([f'B_{sd}_{n}'for n in ['UpperArm','Forearm','Hand']],T,Vector((sign,-.35,0)));rot(f'B_{sd}_Hand',R)
  if role=='Attack':
   t=ease(f/12) if f<=23 else 1-ease((f-23)/10);anchor=anchors[19];home=Vector((.45,-.28,rig.pose.bones['B_L_UpperArm'].head.z-.32));target=home.lerp(anchor['hand'].translation,t)+Vector((0,-.20,.15))*math.sin(math.pi*t);R=handR.to_quaternion().slerp(anchor['hand'].to_quaternion(),t).to_matrix();pole=Vector((1,2,0)).normalized().lerp(Vector((1,0,-.6)).normalized(),t);ik(['B_L_UpperArm','B_L_Forearm','B_L_Hand'],target,pole);rot('B_L_Hand',R)
  for side in ('LR' if role=='Death' else 'R' if role=='Attack' else ''):
   h=rig.pose.bones[f'B_{side}_Hand'];T=h.head.copy();R=h.matrix.to_3x3().copy()
   spine=rig.pose.bones['B_Spine'].matrix.to_3x3()@rig.data.bones['B_Spine'].matrix_local.to_3x3().inverted()
   pole=spine@Vector((1,2,0) if side=='L' else (-1,-.25,0))
   ik([f'B_{side}_{n}'for n in ['UpperArm','Forearm','Hand']],T,pole);rot(f'B_{side}_Hand',R)
  if role=='Death':
   h=rig.pose.bones['B_L_Hand'];bm=h.matrix@g;axis=bm.to_3x3().col[2].normalized();back=bm.to_3x3().col[1].normalized();away=h.head-rig.pose.bones['B_L_Forearm'].head;away=(away-axis*away.dot(axis)).normalized();ang=math.atan2(axis.dot(back.cross(away)),back.dot(away));rot(h.name,Quaternion(axis,ang*(1-w)).to_matrix()@h.matrix.to_3x3())
  if role not in ['Death']:
   targets={}
   for s in 'LR':
    ft=f'B_{s}_Foot';T=rig.pose.bones[ft].head.copy()
    if role in gait:
     T.x= .17 if s=='L' else -.17
     T.y*=.80
     T.z=feet[s]['height']+(.10 if role=='Walking'else .14)*gait[role][f][s]
    else:T.z=feet[s]['height']
    targets[s]=T
   # Lower the pelvis only as much as required for reachable planted feet.
   correction=0
   for s,T in targets.items():
    th,ca,ft=[rig.pose.bones[f'B_{s}_{n}']for n in ['Thigh','Calf','Foot']];length=(ca.head-th.head).length+(ft.head-ca.head).length;dxy=(Vector((T.x,T.y,0))-Vector((th.head.x,th.head.y,0))).length;maxz=math.sqrt(max(.01,(length*.98)**2-dxy*dxy));correction=max(correction,th.head.z-T.z-maxz)
   if correction>0:
    b=rig.pose.bones['B_Pelvis'];m=b.matrix.copy();m.translation.z-=correction;b.matrix=m;bpy.context.view_layer.update()
   for s,T in targets.items():
    ik([f'B_{s}_{n}'for n in ['Thigh','Calf','Foot']],T,Vector((0,-1,0)));rot(f'B_{s}_Foot',feet[s]['R']);rig.pose.bones[f'B_{s}_Toe0'].rotation_quaternion=Quaternion()
   bpy.context.view_layer.update()
  if role=='Death' and 5<f<20:
   h=rig.pose.bones['B_Head'];m=h.matrix.copy();up=rig.pose.bones['B_Spine'].matrix.to_3x3()@rig.data.bones['B_Spine'].matrix_local.to_3x3().inverted()@Vector((0,0,1));m.translation+=up*.020*math.sin(math.pi*(f-5)/15)**2;h.matrix=m;bpy.context.view_layer.update()
  for s in 'LR':anatomy(s)
  # Strings and hidden arrow must be rebuilt after changing the carried bow frame.
  rig.pose.bones['Bow'].rotation_quaternion=Quaternion();rig.pose.bones['Bow'].location=Vector();bpy.context.view_layer.update()
  bm=rig.pose.bones['Bow'].matrix
  mid=bm@Vector((0,.215,.04));tips=[bm@Vector((0,.215,.55)),bm@Vector((0,.215,-.55))]
  if role=='Attack'and 18<=f<=22:
   rh=rig.pose.bones['B_R_Finger11'].head.lerp(rig.pose.bones['B_R_Finger12'].head,.55);nock=mid.lerp(rh,float(np.clip((f-18),0,1)))
  else:nock=mid
  for n,start in zip(['StringTop','StringBottom'],tips):
   d=nock-start;m=d.to_track_quat('Z','Y').to_matrix().to_4x4();m.translation=start;rig.pose.bones[n].matrix=m@Matrix.Scale(d.length,4)@restprop[n]
  d=Vector((0,-1,0)) if role=='Attack' and f>=23 else bm@Vector((0,-.08,.04))-nock;m=d.to_track_quat('Z','Y').to_matrix().to_4x4();m.translation=nock
  rig.pose.bones['Arrow'].matrix=m@Matrix.Scale(1.22,4)@Matrix.Translation((0,0,.32))@restprop['Arrow']
  if not(role=='Attack'and 19<=f<23):rig.pose.bones['Arrow'].scale*=.001
  bpy.context.view_layer.update();out.append(get());intents.append({'frame':f,'feet':{s:list(rig.pose.bones[f'B_{s}_Foot'].head)for s in 'LR'},'right_wrist':list(rig.pose.bones['B_R_Hand'].head)})
 poses[role]=out;intent[role]=intents
poses['Cast']=poses['Attack'];poses['Dead']=[poses['Death'][-1]]*31
for role,rows in poses.items():
 action(None);bpy.data.actions.remove(bpy.data.actions[role]);a=bpy.data.actions.new(role);a.use_fake_user=True;rig.animation_data.action=a;prev={}
 for f,row in enumerate(rows):
  for n,(q,l,s)in row.items():
   if n in prev and prev[n].dot(q)<0:q=-q
   prev[n]=q;b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=s
   for channel in ['rotation_quaternion','location','scale']:b.keyframe_insert(channel,frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 # Continuous roll distribution after the anatomical hinge correction.
 for side in 'LR':
  rb=rig.data.bones;fa,ha,ua=[rb[f'B_{side}_{n}']for n in ['Forearm','Hand','UpperArm']];axes=[(fa.matrix_local.inverted()@ha.head_local).normalized(),(ua.matrix_local.inverted()@fa.head_local).normalized()];angles=[]
  for f in range(len(rows)):
   sc.frame_set(f);rel=(rig.pose.bones[fa.name].matrix.inverted()@rig.pose.bones[ha.name].matrix).to_quaternion();rest=(fa.matrix_local.inverted()@ha.matrix_local).to_quaternion();qs=[rel@rest.inverted(),rig.pose.bones[ua.name].matrix_basis.to_quaternion()];angles.append([math.remainder(2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w),math.tau)for q,axis in zip(qs,axes)])
  for f,vals in enumerate(np.unwrap(angles,axis=0)):
   for kind,axis,value,factor in zip(['ForearmTwist','UpperArmTwist'],axes,vals,[.5,-.5]):
    b=rig.pose.bones[f'B_{side}_{kind}'];ang=float(value*factor)
    ang=float(np.clip(ang,-math.pi/2,math.pi/2)) if kind=='ForearmTwist'else float(np.clip(ang,-math.radians(40),math.radians(40)))
    b.rotation_quaternion=Quaternion(axis,ang);b.keyframe_insert('rotation_quaternion',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
action(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_round3_motion.blend'))
(P/'work/round3_motion.json').write_text(json.dumps(report,indent=2));(P/'work/round3_intent.json').write_text(json.dumps(intent,indent=2))
common.workbench_clay(sc,textured=True)
for role,f in [('Standing',0),('Walking',0),('Walking',6),('Running',6),('Attack',22),('Cast',22)]:
 action(bpy.data.actions[role]);sc.frame_set(f);common.render_views(str(P/f'review/round3_{role}_{f}'),.87,2.45,views=('front','left','three_quarter'),resolution=(560,650))
print('ROUND3_MOTION',report)
