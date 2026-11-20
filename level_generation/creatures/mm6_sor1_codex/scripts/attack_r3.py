"""Spear-Attack1 torso/weight transfer, fitted fixed two-hand grip and continuous IK poles."""
import bpy,sys,json,math,ast,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'review/round3/baseline/work/production_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];scene=bpy.context.scene;scene.render.fps=120
import arm_solver as sol
sides={s:sol.Side('B_'+s+'_') for s in 'LR'};G=sol.G;L=json.loads((p/'work/round2_left_grip.json').read_text());sides['L'].grip_hand=Vector(L['centre']);sides['L'].axis_hand=Vector(L['axis'])
names=[b.name for b in rig.data.bones];robe=[n for n in names if n.startswith('Robe_')]
def attach(a):
 rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def reset(d):
 attach(None)
 for n,m in d.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def smooth(t):
 t=max(0.,min(1.,t));return t*t*t*(10+t*(-15+6*t))
def curve(keys,t):
 if t<=keys[0][0]:return Vector(keys[0][1])
 for (a,x),(b,y) in zip(keys,keys[1:]):
  if t<=b:return Vector(x).lerp(Vector(y),smooth((t-a)/(b-a)))
 return Vector(keys[-1][1])
# Reuse the production discrete-foot IK unchanged.
module=ast.parse((p/'scripts/round2_motion.py').read_text());node=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='leg');exec(compile(ast.Module(body=[node],type_ignores=[]),'round2_motion.py','exec'))
attach(bpy.data.actions['Standing']);scene.frame_set(0);stand={n:rig.pose.bones[n].matrix_basis.copy() for n in names};feet={s:rig.pose.bones['B_'+s+'_Foot'].matrix.copy() for s in 'LR'}
standWorld={n:rig.pose.bones[n].matrix.copy() for n in names}
H0={s:rig.pose.bones['B_'+s+'_Hand'].matrix.copy() for s in 'LR'};P0={s:rig.pose.bones['B_'+s+'_Forearm'].head-rig.pose.bones['B_'+s+'_UpperArm'].head for s in 'LR'};C0=H0['R']@sides['R'].grip_hand;A0=(H0['R'].to_3x3()@sides['R'].axis_hand).normalized()
source=json.loads((p/'work/source_spear_r3.json').read_text());src=[{n:Matrix(m) for n,m in row.items()} for row in source['poses']]
# Smoothly resample the 30 Hz library rotations; no rounded nearest-frame sampling.
def source_m(n,f):
 i=min(35,max(0,int(f)));w=min(1,max(0,f-i));a,b=src[i][n],src[i+1][n];m=a.to_quaternion().slerp(b.to_quaternion(),w).to_matrix().to_4x4();m.translation=a.translation.lerp(b.translation,w);return m
N=300;frames=[];spacing=.50;shift=.47
for f in range(N+1):
 t=f/120;reset(stand);rawrobe={n:rig.pose.bones[n].matrix.copy() for n in robe};before={n:rig.pose.bones[n].head.copy() for n in ['B_Pelvis',*[f'B_{s}_{b}' for s in 'LR' for b in ['Calf','Foot']]]}
 blend=smooth(t/.55)*smooth((2.5-t)/.55)
 sf=curve([(0,(0,0,0)),(.55,(0,0,0)),(1.,(10,0,0)),(1.45,(16,0,0)),(1.68,(22,0,0)),(2.15,(36,0,0)),(2.5,(36,0,0))],t).x
 # Preserve the library's torso turn, recoil and follow-through around our upright standing frame.
 for n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
  base=src[0][n];d=source_m(n,sf).to_quaternion()@base.to_quaternion().inverted();e=d.to_euler('XYZ');e.z=0;d=e.to_quaternion();pb=rig.pose.bones[n];m=pb.matrix.copy();q=Quaternion().slerp(d,.50*blend);M=(q@standWorld[n].to_quaternion()).to_matrix().to_4x4();M.translation=m.translation;pb.matrix=M;bpy.context.view_layer.update()
 # A left-leading stance permits separated grip thirds without a crossed wrist.
 for n in ['B_Spine','B_Spine1','B_Spine2']:
  pb=rig.pose.bones[n];m=pb.matrix.copy();q=Quaternion((0,0,1),math.radians(-65)/3*blend);M=(q@m.to_quaternion()).to_matrix().to_4x4();M.translation=m.translation;pb.matrix=M;bpy.context.view_layer.update()
 for n in ['B_Neck','B_Head']:
  pb=rig.pose.bones[n];m=pb.matrix.copy();q=Quaternion((0,0,1),math.radians(65)/2*blend);M=(q@m.to_quaternion()).to_matrix().to_4x4();M.translation=m.translation;pb.matrix=M;bpy.context.view_layer.update()
 motion=curve([(0,(0,0,0)),(.55,(0,.015,-.015)),(1.,(0,.02,-.035)),(1.45,(0,-.30,-.055)),(1.68,(0,-.295,-.05)),(2.25,(0,0,0)),(2.5,(0,0,0))],t)
 pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation+=motion;pb.matrix=m;bpy.context.view_layer.update()
 for sd in 'LR':
  m=feet[sd].copy()
  if sd=='L':m.translation+=curve([(0,(0,0,0)),(.55,(0,0,0)),(.76,(0,-.14,.05)),(.98,(0,-.28,0)),(1.70,(0,-.28,0)),(1.93,(0,-.14,.05)),(2.16,(0,0,0)),(2.5,(0,0,0))],t)
  leg(sd,m)
 after={n:rig.pose.bones[n].head.copy() for n in before}
 for n in robe:
  z=rig.data.bones[n].head_local.z;x=rig.data.bones[n].head_local.x;mix=max(0,min(1,.5+x/.4));dp=after['B_Pelvis']-before['B_Pelvis'];dk=(after['B_R_Calf']-before['B_R_Calf']).lerp(after['B_L_Calf']-before['B_L_Calf'],mix);df=(after['B_R_Foot']-before['B_R_Foot']).lerp(after['B_L_Foot']-before['B_L_Foot'],mix)
  delta=df.lerp(dk,max(0,min(1,(z-.10)/.48))) if z<.58 else dk.lerp(dp,max(0,min(1,(z-.58)/.46)));m=rawrobe[n].copy();m.translation+=delta;rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
 gp=curve([(0,C0),(.55,(-.36,-.10,1.36)),(1.,(-.36,-.04,1.36)),(1.45,(-.33,-.34,1.38)),(1.68,(-.33,-.335,1.38)),(2.05,(-.49,-.18,1.30)),(2.5,C0)],t)
 ax=curve([(0,A0),(.65,(.23,-.971,.065)),(1.75,(.23,-.971,.065)),(2.5,A0)],t).normalized()
 weight=smooth((t-.40)/.38)*smooth((2.18-t)/.30)
 poles={s:P0[s].normalized().lerp(Vector(((-1 if s=='R' else 1),.35,-.7)).normalized(),smooth(t/.65)*smooth((2.5-t)/.65)) for s in 'LR'}
 frames.append({'t':t,'pose':{n:rig.pose.bones[n].matrix_basis.copy() for n in names},'gp':gp,'ax':ax,'w':weight,'poles':poles,'motion':motion})
# Select one roll per hand for the entire held phase, not an independently quantised roll at every key.
def pose_cost(r,side):
 sw,tw=r['sw'],r['tw'];raw=r['tw0'];sgn=-1 if side.s=='B_R_' else 1
 return sw*sw+tw*tw+40*max(0,sw-50)**2+1000*max(0,abs(raw)-120)**2+1e8*r['miss']**2+2e6*max(0,r['E'].z-r['W'].z+.06)**2+5e6*max(0,(.23 if sgn<0 else .10)-sgn*r['E'].x)**2
def hand_pose(side,target,Rh,P,w):
 r=side.pose_anatomical(target,Rh,P)
 if side.s=='B_L_' and w<.999999:
  F=r['Ra']@side.rel['Forearm'];d=(r['W']-r['E']).normalized();F=(F@side.uF).rotation_difference(d).to_matrix()@F;neutral=F@side.rel['Hand'];Rh=neutral.to_quaternion().slerp(Rh.to_quaternion(),w).to_matrix();r=side.pose_anatomical(r['W']+Rh@side.grip_hand,Rh,P)
 return r
from sleeve_fit_r2 import Sleeve
sleeve=Sleeve(rig,body,'B_L_')
phis={}
for sd in 'RL':
 side=sides[sd];costs=np.zeros(72)
 for f in [96,120,138,156,174,189]:
  row=frames[f];reset(row['pose']);A=row['ax'];C=row['gp']+(A*spacing if sd=='L' else Vector());S=rig.pose.bones[side.s+'UpperArm'].head;axis=(C-S).normalized();q0=(side.rest['Hand']@side.axis_hand).rotation_difference(A).to_matrix()
  if sd=='L':sleeve.begin()
  for k in range(72):
   phi=k*2*math.pi/72;Rh=Quaternion(A,phi).to_matrix()@q0@side.rest['Hand'];vals=[]
   for angle in range(-180,180,15):
    P=Quaternion(axis,math.radians(angle))@Vector((0,0,-1));r=side.pose_anatomical(C,Rh,P);cost=pose_cost(r,side)
    if sd=='L':
     sleeve.cost(r,C,A,{});cost+=200000*max(0,sleeve.stretch-1.82)**2
    vals.append(cost)
   costs[k]+=min(vals)
 phis[sd]=int(costs.argmin())*2*math.pi/72
print('FIXED_ROLL',phis,flush=True)
# Solve a continuous elbow plane, using a periodic angle about shoulder-to-wrist, then smooth its path.
plane={s:[] for s in 'LR'}
for row in frames:
 reset(row['pose']);t=row['t'];A=row['ax'];C=row['gp'];w=row['w']
 for sd in 'RL':
  side=sides[sd];q0=(side.rest['Hand']@side.axis_hand).rotation_difference(A).to_matrix();Rh=Quaternion(A,phis[sd]).to_matrix()@q0@side.rest['Hand'];active=smooth(t/.65)*smooth((2.5-t)/.65) if sd=='R' else w;Rh=H0[sd].to_quaternion().slerp(Rh.to_quaternion(),active).to_matrix() if sd=='R' else Rh
  free=curve([(0,H0['L'].translation),(.38,(.34,-.38,1.18)),(.70,(.20,-.57,1.36)),(1.8,(.20,-.60,1.36)),(2.17,(.34,-.38,1.18)),(2.5,H0['L'].translation)],t)+row['motion'];target=C if sd=='R' else (free+Rh@side.grip_hand).lerp(C+A*spacing,w);S=rig.pose.bones[side.s+'UpperArm'].head;axis=(target-S).normalized();best=None
  if sd=='L':sleeve.begin()
  for angle in range(-180,180,5):
   a=math.radians(angle);P=Quaternion(axis,a)@Vector((0,0,-1));r=hand_pose(side,target,Rh,P,w);cost=pose_cost(r,side)
   if sd=='L':
    sleeve.cost(r,C+A*spacing,A,{});cost+=200000*max(0,sleeve.stretch-1.82)**2
   if plane[sd]:cost+=5000*((a-plane[sd][-1]+math.pi)%(2*math.pi)-math.pi)**2
   if best is None or cost<best[0]:best=(cost,a)
  plane[sd].append(best[1])
for sd in 'LR':
 a=np.unwrap(np.array(plane[sd]));radius=10;ww=np.exp(-np.arange(-radius,radius+1)**2/(2*4.0**2));ww/=ww.sum();a=np.convolve(np.pad(a,(radius,radius),mode='edge'),ww,mode='valid');plane[sd]=a
old=bpy.data.actions['Attack'];old.name='OldAttack';out=bpy.data.actions.new('Attack');out.use_fake_user=True;out.use_frame_range=True;out.frame_start=0;out.frame_end=N;intent=[];helpers={};prevTw={}
for f,row in enumerate(frames):
 reset(row['pose']);t=row['t'];A=row['ax'];C=row['gp'];w=row['w'];results={}
 for sd in 'RL':
  side=sides[sd];q0=(side.rest['Hand']@side.axis_hand).rotation_difference(A).to_matrix();Rh=Quaternion(A,phis[sd]).to_matrix()@q0@side.rest['Hand'];active=smooth(t/.65)*smooth((2.5-t)/.65) if sd=='R' else w
  Rh=H0[sd].to_quaternion().slerp(Rh.to_quaternion(),active).to_matrix() if sd=='R' else Rh
  if sd=='R':target=C
  else:
   free=curve([(0,H0['L'].translation),(.38,(.34,-.38,1.18)),(.70,(.20,-.57,1.36)),(1.8,(.20,-.60,1.36)),(2.17,(.34,-.38,1.18)),(2.5,H0['L'].translation)],t)+row['motion'];target=(free+Rh@side.grip_hand).lerp(C+A*spacing,w)
  S=rig.pose.bones[side.s+'UpperArm'].head;P=Quaternion((target-S).normalized(),float(plane[sd][f]))@Vector((0,0,-1));P=P0[sd].normalized().lerp(P,smooth(t/.25)*smooth((2.5-t)/.25));r=hand_pose(side,target,Rh,P,w);prevTw[sd]=r['tw0'];side.apply(r);results[sd]=r
  for n,q in (G['finger_local'] if sd=='R' else L['fingers']).items():rig.pose.bones[n].rotation_quaternion=Quaternion(q) if sd=='R' else Quaternion().slerp(Quaternion(q),w)
 # Slide to the lower-third rear grip during preparation, hold its frame through the thrust, and reset during recovery.
 sb=rig.pose.bones['B_Staff'];M=sb.matrix.copy();M.translation+=(rig.pose.bones['B_R_Hand'].matrix.to_3x3()@sides['R'].axis_hand).normalized()*shift*smooth(t/.65)*smooth((2.5-t)/.65);sb.matrix=M;bpy.context.view_layer.update()
 for sd in 'LR':
  fb,hb=[rig.data.bones[f'B_{sd}_{b}'] for b in ['Forearm','Hand']];axis=(fb.matrix_local.inverted()@hb.head_local).normalized();dq=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion()@(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion().inverted()
  def twist(q,a):return (2*math.atan2(Vector((q.x,q.y,q.z)).dot(a),q.w)+math.pi)%(2*math.pi)-math.pi
  for n,axis,a in [(f'B_{sd}_ForearmTwist',axis,.5*twist(dq,axis)),(f'B_{sd}_UpperArmTwist',(rig.data.bones[f'B_{sd}_UpperArm'].matrix_local.inverted()@fb.head_local).normalized(),0)]:
   if 'Upper' in n:a=-.5*twist(rig.pose.bones[f'B_{sd}_UpperArm'].matrix_basis.to_quaternion(),axis)
   if n in helpers:a+=round((helpers[n]-a)/(2*math.pi))*2*math.pi
   helpers[n]=a;rig.pose.bones[n].rotation_quaternion=Quaternion(axis,a)
 pose={n:rig.pose.bones[n].matrix_basis.copy() for n in names};attach(out)
 for n,m in pose.items():
  pb=rig.pose.bones[n];pb.matrix_basis=m;pb.rotation_mode='QUATERNION';pb.keyframe_insert('rotation_quaternion',frame=f)
  if n=='B_Pelvis' or n=='B_Staff' or n in robe:pb.keyframe_insert('location',frame=f)
 intent.append({'t':t,'weight':w,'axis':list(A),'right_grip':list(C),'left_grip':list(C+A*spacing),'miss_mm':{s:results[s]['miss']*1000 for s in 'LR'},'wrist_swing':{s:results[s]['sw'] for s in 'LR'}})
# Align the palm while clear of the shaft, close after arriving, and open before withdrawing.
attach(out);side=sides['L'];leftNames=[n for n in names if n.startswith('B_L_') and any(k in n for k in ['UpperArm','Forearm','Hand'])];poles={};saved={}
for frame in [94,201]:
 scene.frame_set(frame);poles[frame]=rig.pose.bones['B_L_Forearm'].head-rig.pose.bones['B_L_UpperArm'].head

def key_left(r,frame):
 side.apply(r,frame)
 for kind in ['Forearm','UpperArm']:
  b=rig.data.bones['B_L_'+kind];child=rig.data.bones['B_L_'+('Hand' if kind=='Forearm' else 'Forearm')];axis=(b.matrix_local.inverted()@child.head_local).normalized()
  dq=(rig.pose.bones[b.name].matrix.inverted()@rig.pose.bones[child.name].matrix).to_quaternion()@(b.matrix_local.inverted()@child.matrix_local).to_quaternion().inverted() if kind=='Forearm' else rig.pose.bones[b.name].matrix_basis.to_quaternion()
  angle=twist(dq,axis)*(.5 if kind=='Forearm' else -.5);pb=rig.pose.bones['B_L_'+kind+'Twist'];pb.rotation_quaternion=Quaternion(axis,angle);pb.keyframe_insert('rotation_quaternion',frame=frame)
for frame in [*range(66,94),*range(202,222)]:
 scene.frame_set(frame);H=rig.pose.bones['B_R_Hand'].matrix;C=H@sides['R'].grip_hand;A=(H.to_3x3()@sides['R'].axis_hand).normalized();q0=(side.rest['Hand']@side.axis_hand).rotation_difference(A).to_matrix();Rh=Quaternion(A,phis['L']).to_matrix()@q0@side.rest['Hand'];radial=Rh@side.grip_hand;radial=(radial-A*radial.dot(A)).normalized();offset=.12*(smooth((94-frame)/28) if frame<94 else smooth((frame-201)/20));target=C+A*spacing-radial*offset;r=side.pose_anatomical(target,Rh,poles[94 if frame<94 else 201]);key_left(r,frame)
for frame in [66,221]:
 scene.frame_set(frame);saved[frame]={n:rig.pose.bones[n].rotation_quaternion.copy() for n in leftNames}
for frame in [*range(66),*range(222,N+1)]:
 scene.frame_set(frame);mix=smooth((frame-12)/54) if frame<66 else smooth((280-frame)/(280-221));end=saved[66 if frame<66 else 221]
 for n in leftNames:
  pb=rig.pose.bones[n];pb.rotation_quaternion=stand[n].to_quaternion().slerp(end[n],mix);pb.keyframe_insert('rotation_quaternion',frame=frame)
 bpy.context.view_layer.update();H=rig.pose.bones['B_L_Hand'].matrix.copy();S=rig.pose.bones['B_L_UpperArm'].head;E=rig.pose.bones['B_L_Forearm'].head;key_left(side.pose_anatomical(H@side.grip_hand,H.to_3x3(),E-S),frame)
for frame in range(N+1):
 scene.frame_set(frame);close=smooth((frame-94)/14)*smooth((201-frame)/12)
 for n,q in L['fingers'].items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=stand[n].to_quaternion().slerp(Quaternion(q),close);pb.keyframe_insert('rotation_quaternion',frame=frame)
bpy.data.actions.remove(old)
# The new all-clip gate also caught a small onset pop in Fidget; smooth only that free-arm onset.
act=bpy.data.actions['Fidget'];attach(act)
curves=[fc for layer in act.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
for bone in ['B_L_UpperArm','B_L_Forearm','B_L_UpperArmTwist','B_L_ForearmTwist']:
 comps={fc.array_index:fc for fc in curves if fc.data_path==f'pose.bones["{bone}"].rotation_quaternion'}
 if len(comps)!=4:continue
 raw=[Quaternion([comps[k].keyframe_points[i].co.y for k in range(4)]) for i in range(len(comps[0].keyframe_points))]
 for i in range(1,min(30,len(raw)-1)):
  avg=raw[max(0,i-2)].slerp(raw[min(len(raw)-1,i+2)],.5);q=raw[i].slerp(avg,.65*smooth(i/4)*smooth((30-i)/6))
  for k in range(4):comps[k].keyframe_points[i].co.y=q[k]
 for fc in comps.values():fc.update()
runpy.run_path(str(p/'scripts/normalize_keys_r2.py'));attach(bpy.data.actions['Standing']);scene.frame_set(0)
(p/'work/round3_attack_intent.json').write_text(json.dumps({'source':'anim_library/humanoid_set/2Hand Spear.glb:2HandSpearAttack1','grip_spacing_m':spacing,'staff_slide_m':shift,'fixed_roll':phis,'frames':intent},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round3_motion.blend'))
import common
common.workbench_clay(scene,textured=True);attach(bpy.data.actions['Attack'])
for i,t in enumerate([0,.53,.67,1.,1.2,1.45,1.68,2.1,2.5]):
 scene.frame_set(int(t*120),subframe=(t*120)%1);common.render_views(str(p/'review/round3'/f'attack_try_{i}'),.95,2.6,views=('front','left'),resolution=(420,600))
