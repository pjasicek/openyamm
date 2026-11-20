"""Fit MM8 diagonal carry and one-hand source chop with fixed-length chains and a separate axe joint."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik,common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_motion.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'RL'};names=list(r.pose.bones.keys());roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
def act(a):
 r.animation_data_create();r.animation_data.action=a
 if a and len(a.slots):r.animation_data.action_slot=a.slots[0]
def update():bpy.context.view_layer.update()
def world(n):return armik.W(r,n).copy()
def snap():return {n:r.pose.bones[n].matrix_basis.copy() for n in names}
def apply(row):
 act(None)
 for n,m in row.items():r.pose.bones[n].matrix_basis=m
 update()
def blend(a,b,t):
 q=a.to_quaternion().slerp(b.to_quaternion(),t);m=q.to_matrix().to_4x4();m.translation=a.translation.lerp(b.translation,t);return m
def smooth_path(path,mode='edge',constant=False):
 out=[dict(x) for x in path]
 for key in ['phi','psi']:
  v=np.unwrap(np.radians([x[key] for x in path]));v=np.full_like(v,np.median(v)) if constant else np.convolve(np.pad(v,(3,3),mode=mode),np.array([1,6,15,20,15,6,1])/64,mode='valid')
  for row,x in zip(out,np.degrees(v)):row[key]=float(x)
 return out
def limit_free_wrist(sd):
 p=r.pose.bones[f'B_{sd}_Hand'];q=p.matrix_basis.to_quaternion();sw,tw=armik.split_swing_twist(q,Vector((0,1,0)))
 if sw.w<0:sw=-sw
 ax,ang=sw.to_axis_angle();p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion(ax,min(ang,math.radians(58)))@Quaternion((0,1,0),max(-math.radians(85),min(math.radians(85),tw)));update()
raw={}
for nm in roles:
 a=bpy.data.actions[nm];act(a);rows=[]
 for f in range(round(a.frame_range[1])+1):sc.frame_set(f);rows.append(snap())
 raw[nm]=rows
base=raw['Standing'][0]
for row in raw['Hit']:
 for n in names:
  if any(k in n for k in ['Spine','Clavicle','Neck','Head']):row[n]=blend(base[n],row[n],.4)
apply(base);C0=world('B_Spine2');pel0=world('B_Pelvis').translation
RESTPEL=r.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();rest=np.array([v.co[:] for v in body.data.vertices]);footids=np.where(rest[:,2]<.09)[0]
CARRY=Vector((-.14,-.39,1.04));AXIS=Vector((.84,-.22,.50)).normalized();GRIP_Z=.24;SPACE=.34
# Keep the source's arm/trunk chop; reduce the human's deep knee crouch for the native planted bull stance.
for nm in ['Attack','Hit']:
 for row in raw[nm]:
  for n in names:
   if n=='B_Pelvis' or any(k in n for k in ['Thigh','Calf','Foot','Toe']):row[n]=blend(base[n],row[n],.15 if nm=='Attack' else .3)
# One-shot recoil returns to the actual idle pose.
for nm in ['Hit','Fidget']:
 for i,row in enumerate(raw[nm]):
  t=i/(len(raw[nm])-1);u=max(0,min(1,t/.18,(1-t)/.18));u=u*u*(3-2*u);raw[nm][i]={n:blend(base[n],row[n],u) for n in names}
# Fit carried actions first; their actual wrist/hand endpoints seed the one-hand transitions.
result={};props={};stats={}
def meshco():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();return a
ng=[g.name for g in body.vertex_groups]
FOOT_MASK={sd:np.array([sum(g.weight for g in v.groups if ng[g.group] in (f'B_{sd}_Foot',f'B_{sd}_Toe0'))>.5 for v in body.data.vertices]) for sd in 'LR'}
def leg_ik(s,target,pole_target=None):
 hn,kn,an=[f'B_{s}_{k}' for k in ('Thigh','Calf','Foot')]
 mh,mk,ma=[r.pose.bones[n].matrix.copy() for n in (hn,kn,an)];h,k,a=[m.translation.copy() for m in (mh,mk,ma)]
 l1,l2=(k-h).length,(a-k).length;u=(target-h).normalized();dist=min((target-h).length,(l1+l2)*.999)
 old=(a-h).normalized();pole=(k-h)-old*(k-h).dot(old);pole=old.rotation_difference(u)@pole;pole=(pole-u*pole.dot(u)).normalized()
 if pole_target is not None:
  pole=pole_target-h;pole=(pole-u*pole.dot(u)).normalized()
 ca=max(-1,min(1,(l1*l1+dist*dist-l2*l2)/(2*l1*dist)));newk=h+l1*(u*ca+pole*math.sqrt(1-ca*ca))
 q=(k-h).rotation_difference(newk-h);m=q.to_matrix().to_4x4()@mh;m.translation=h;r.pose.bones[hn].matrix=m;bpy.context.view_layer.update()
 mk2=r.pose.bones[kn].matrix.copy();a2=r.pose.bones[an].head.copy();q=(a2-mk2.translation).rotation_difference(target-mk2.translation);m=q.to_matrix().to_4x4()@mk2;m.translation=mk2.translation;r.pose.bones[kn].matrix=m;bpy.context.view_layer.update()
 m=r.pose.bones[an].matrix.copy();at=m.translation.copy();m=ma.copy();m.translation=at;r.pose.bones[an].matrix=m;bpy.context.view_layer.update()

def plant_both():
 for _ in range(3):
  c=meshco();targets={s:r.pose.bones[f'B_{s}_Foot'].head.copy() for s in 'LR'}
  for s,t in targets.items():t.z-=float(c[FOOT_MASK[s],2].min())
  # Lower the pelvis just enough for both fixed-length legs to reach their grounded soles.
  for it in range(30):
   reach=[]
   for s,t in targets.items():
    h,k,a=[r.pose.bones[f'B_{s}_{n}'].head for n in ('Thigh','Calf','Foot')];reach.append((t-h).length/((k-h).length+(a-k).length))
   if max(reach)<.997:break
   m=r.pose.bones['B_Pelvis'].matrix.copy();m.translation.z-=.004;r.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
  for s,t in targets.items():leg_ik(s,t)

for nm in ['Standing','Walking','Running','Hit','Fidget']:
 rows=raw[nm];frames=[]
 for row in rows:
  apply(row);ch=world('B_Spine2');D=ch.to_3x3()@C0.to_3x3().inverted();C=ch.translation+D@(CARRY-C0.translation);A=(D@AXIS).normalized();frames.append({'snap':row,'C':C,'dir':A})
 fit=[{n:m.copy() for n,m in row.items()} for row in rows]
 for sd in 'RL':
  axis=Vector(G[sd]['handle_axis_hand_local']);centre=Vector(G[sd]['handle_centre_hand_local']);armframes=[]
  for i,fr in enumerate(frames):
   apply(fit[i]);C=fr['C']+(fr['dir']*SPACE if sd=='L' else Vector());R,_,_,_=armik.hand_for_axis(r,sd,axis,fr['dir']);armframes.append({'snap':snap(),'wrist':C-R@centre,'dir':fr['dir'],'centre':C})
  path=armik.arm_dp(r,sd,armframes,axis,phis=range(-90,91,15),psis=range(0,360,10),k_twist=.6,k_dphi=1,k_dpsi=.8)
  path=smooth_path(path,mode='wrap' if nm in ['Standing','Walking','Running'] else 'edge',constant=nm=='Standing')
  vals=[]
  for i,(fr,choice) in enumerate(zip(armframes,path)):
   H=armik.hand_rot(axis,fr['dir'],choice['psi']);wrist=fr['centre']-H@centre
   sw,tw=armik.apply_arm(r,sd,fr['snap'],wrist,axis,fr['dir'],choice['phi'],choice['psi'])
   for n,q in G[sd]['finger_local'].items():r.pose.bones[n].rotation_mode='QUATERNION';r.pose.bones[n].rotation_quaternion=Quaternion(q)
   update();fit[i]=snap();error=(world(f'B_{sd}_Hand')@centre-fr['centre']).length;vals.append((sw,tw,error))
  stats[nm+sd]={'wrist_swing_max_deg':max(v[0] for v in vals),'twist_range_deg':[min(v[1] for v in vals),max(v[1] for v in vals)],'grip_error_m':max(v[2] for v in vals)}
 result[nm]=fit;props[nm]=frames;print('CARRY',nm,stats[nm+'R'],stats[nm+'L'],flush=True)
standing=result['Standing'][0]
# The single-handed attack keeps the selected source's hand orientation and trajectory.
for nm in ['Attack','Death']:
 result[nm]=[];props[nm]=[]
 for i,row in enumerate(raw[nm]):
  t=i/(len(raw[nm])-1);edge=min(1,t/.18,(1-t)/.20) if nm=='Attack' else min(1,t/.12);edge=max(0,edge);edge=edge*edge*(3-2*edge)
  pose={n:blend(standing[n],row[n],edge) for n in names};apply(pose)
  for sd in 'RL':
   for n,q in G[sd]['finger_local'].items():
    r.pose.bones[n].rotation_mode='QUATERNION';r.pose.bones[n].rotation_quaternion=Quaternion(q).slerp(Quaternion(G[sd]['open_finger_local'][n]),1 if sd=='L' and nm=='Death' else (min(1,edge/.35) if sd=='L' else 0))
  update();H=world('B_R_Hand');C=H@Vector(G['R']['handle_centre_hand_local']);A=(H.to_3x3()@Vector(G['R']['handle_axis_hand_local'])).normalized()
  result[nm].append(snap());props[nm].append({'C':C,'dir':A})
# Release before the wind-up; the free hand counterbalances outside the left shoulder.
frames=[];axis=Vector(G['L']['handle_axis_hand_local']);centre=Vector(G['L']['handle_centre_hand_local']);apply(standing);HL0=world('B_L_Hand');gc=HL0.to_3x3()@centre;away=(-gc+AXIS*gc.dot(AXIS)).normalized();start=HL0@centre+away*.03
for i,row in enumerate(result['Attack']):
 apply(row);H=world('B_R_Hand');CA=H@Vector(G['R']['handle_centre_hand_local']);AA=(H.to_3x3()@Vector(G['R']['handle_axis_hand_local'])).normalized();ch=world('B_Spine2');D=ch.to_3x3()@C0.to_3x3().inverted();guard=ch.translation+D@(Vector((.45,-.40,1.30))-C0.translation);enter=min(1,i/4);enter=enter*enter*(3-2*enter);ret=max(0,min(1,(i-18)/6));ret=ret*ret*(3-2*ret);adopt=min(1,ret/.7);C=start.lerp(guard,enter).lerp(CA+AA*SPACE+away*.06*(1-adopt),adopt);A=(D@AXIS).lerp(AA,adopt).normalized();R,_,_,_=armik.hand_for_axis(r,'L',axis,A)
 frames.append({'snap':row,'wrist':C-R@centre,'dir':A,'centre':C,'ret':ret,'adopt':adopt})
path=smooth_path(armik.arm_dp(r,'L',frames,axis,phis=range(-90,91,15),psis=range(0,360,10),k_twist=.6,k_dphi=1,k_dpsi=.8))
for i,(fr,ch) in enumerate(zip(frames,path)):
 targetR=AXIS.rotation_difference(fr['dir']).to_matrix()@HL0.to_3x3();d=fr['dir'];up=Vector((0,0,1));e=(up-d*up.dot(d)).normalized();fl=Vector((0,1,0))-axis*axis.y;fl.normalize();fw=targetR@fl;goal=math.degrees(math.atan2(fw.dot(d.cross(e)),fw.dot(e)));psi=ch['psi']+((goal-ch['psi']+180)%360-180)*fr['adopt'];phi=ch['phi']*(1-fr['adopt']);R=armik.hand_rot(axis,d,psi);armik.apply_arm(r,'L',fr['snap'],fr['centre']-R@centre,axis,d,phi,psi)
 for n,q in G['L']['finger_local'].items():r.pose.bones[n].rotation_quaternion=Quaternion(G['L']['open_finger_local'][n]).slerp(Quaternion(q),max(0,(fr['ret']-.74)/.26))
 update();result['Attack'][i]=snap()
result['Attack'][-1]=standing
released=result['Attack'][0];result['Attack']=[standing,{n:blend(standing[n],released[n],.5) for n in names}]+result['Attack']
# Keep the retained axe outside the torso and above the floor during the backward fall.
frames=[]
for i,row in enumerate(result['Death']):
 apply(row);t=i/(len(result['Death'])-1);release=max(0,min(1,(t-.08)/.15));release=release*release*(3-2*release);HL=world('B_L_Hand');armik.solve(r,'L',HL.translation+Vector((.15,-.08,.10))*release+away*.03*(1-release),hand_rot=HL.to_3x3());limit_free_wrist('L');row=snap();u=max(0,min(1,(t-.20)/.40));u=u*u*(3-2*u);H=world('B_R_Hand');axis=Vector(G['R']['handle_axis_hand_local']);centre=Vector(G['R']['handle_centre_hand_local']);C=H@centre;A=(H.to_3x3()@axis).normalized();A=A.lerp(Vector((0,-1,.05)).normalized(),u).normalized();C+=Vector((-.25*u,0,.12*u));C.z=max(C.z,.31*u)
 R,_,_,_=armik.hand_for_axis(r,'R',axis,A);frames.append({'snap':row,'wrist':C-R@centre,'dir':A,'centre':C,'u':u})
path=smooth_path(armik.arm_dp(r,'R',frames,axis,phis=range(-90,91,15),psis=range(0,360,10),k_twist=.6,k_dphi=1,k_dpsi=.8))
for i,(fr,choice) in enumerate(zip(frames,path)):
 R=armik.hand_rot(axis,fr['dir'],choice['psi']);sw,tw=armik.apply_arm(r,'R',fr['snap'],fr['centre']-R@centre,axis,fr['dir'],choice['phi'],choice['psi']);fixed=snap();result['Death'][i]={n:blend(fr['snap'][n],fixed[n],min(1,fr['u']*3)) for n in names}
released=result['Death'][0];result['Death']=[standing,{n:blend(standing[n],released[n],.5) for n in names}]+result['Death']
# Bake the prop; each blade face remains in a consistent hand-local frame.
apply(standing);bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT');eb=r.data.edit_bones.new('Axe');eb.head=(0,0,0);eb.tail=(0,0,.2);eb.parent=r.data.edit_bones['B_R_Hand'];bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(P/'work/axe.blend'),link=False) as (src,dst):dst.objects=['Axe']
axe=dst.objects[0];bpy.context.collection.objects.link(axe);axe.name='AxeMesh';g=axe.vertex_groups.new(name='Axe');g.add(list(range(len(axe.data.vertices))),1,'REPLACE');mod=axe.modifiers.new('Rigid axe','ARMATURE');mod.object=r;axe.parent=r
# Initial broad face points toward the party; its axial roll is evaluated on the cutting stroke next.
apply(standing);H0=world('B_R_Hand').to_3x3();Y=Vector((0,-1,0));Y=(Y-AXIS*Y.dot(AXIS)).normalized();X=Y.cross(AXIS).normalized();localX=H0.inverted()@X
for nm,rows in result.items():
 bpy.data.actions.remove(bpy.data.actions[nm]);a=bpy.data.actions.new(nm);a.use_fake_user=True;last={}
 for f,row in enumerate(rows):
  apply(row)
  # Rigid cloven hooves retain source yaw, while the standing feet are level.
  if nm not in ['Walking','Running'] and (nm!='Death' or f<18):
   for sd in 'RL':
    pb=r.pose.bones[f'B_{sd}_Foot'];M=world(pb.name);R0=r.data.bones[pb.name].matrix_local.to_3x3();D=M.to_3x3()@R0.inverted();yaw=math.atan2(D[1][0],D[0][0]);armik.set_world(r,pb.name,armik.rot_world(M,Matrix.Rotation(yaw,3,'Z')@R0));r.pose.bones[f'B_{sd}_Toe0'].matrix_basis.identity()
  if nm in ['Standing','Hit','Attack'] or (nm=='Death' and f<3):plant_both()
  # Recompute twist distribution after the carry solve, preserving the fitted weights.
  for sd in 'RL':
   fb=r.data.bones[f'B_{sd}_Forearm'];hb=r.data.bones[f'B_{sd}_Hand'];ub=r.data.bones[f'B_{sd}_UpperArm']
   axis=(fb.matrix_local.inverted()@hb.head_local).normalized();dq=(r.pose.bones[fb.name].matrix.inverted()@r.pose.bones[hb.name].matrix).to_quaternion()@(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion().inverted();_,tw=armik.split_swing_twist(dq,axis);r.pose.bones[f'B_{sd}_ForearmTwist'].rotation_mode='QUATERNION';r.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.5*tw)
   axis=(ub.matrix_local.inverted()@fb.head_local).normalized();_,tw=armik.split_swing_twist(r.pose.bones[ub.name].matrix_basis.to_quaternion(),axis);r.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_mode='QUATERNION';r.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*tw)
  update();posed=meshco();dz=-float(posed[:,2].min() if nm=='Death' else posed[footids,2].min());dz=max(0,dz) if nm=='Running' else dz;r.pose.bones['B_Pelvis'].location+=RESTPEL@Vector((0,0,dz));update()
  H=world('B_R_Hand');C=H@Vector(G['R']['handle_centre_hand_local']);A=(H.to_3x3()@Vector(G['R']['handle_axis_hand_local'])).normalized();X=H.to_3x3()@localX;X=(X-A*X.dot(A)).normalized();Y=A.cross(X);m=Matrix((X,Y,A)).transposed().to_4x4();m.translation=C-A*GRIP_Z;r.pose.bones['Axe'].matrix=m@r.data.bones['Axe'].matrix_local;update();act(a)
  for n in names+['Axe']:
   pb=r.pose.bones[n];pb.rotation_mode='QUATERNION';q=pb.matrix_basis.to_quaternion()
   if n in last and q.dot(last[n])<0:q=-q
   pb.rotation_quaternion=q;pb.scale=(1,1,1);last[n]=q.copy();pb.keyframe_insert('rotation_quaternion',frame=f)
   if n in ['B_Pelvis','Axe']:pb.keyframe_insert('location',frame=f)
  act(None)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/'review/pilot_fit.json').write_text(json.dumps(stats,indent=2));act(bpy.data.actions['Standing']);sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilots.blend'));common.workbench_clay(sc)
for nm in roles:
 act(bpy.data.actions[nm]);N=round(r.animation_data.action.frame_range[1])
 for i in range(5):
  sc.frame_set(round(N*i/4));common.render_views(str(P/f'review/pilot_{nm}_{i}'),.8 if nm=='Death' else 1.05,4.0 if nm=='Death' else 3.1,views=('front','left','three_quarter'),resolution=(340,480))
