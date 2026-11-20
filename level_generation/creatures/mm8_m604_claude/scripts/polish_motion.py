"""Weapon carry, native-length attack wind-up and smooth one-shot stance transitions."""
from pathlib import Path
import bpy,json,math,numpy as np,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import armik
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/texture_master.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;scene.render.fps=30;names=[b.name for b in rig.data.bones]
G=json.load(open(p/'work/grip_pose.json'))
def set_act(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 set_act(a);scene.frame_set(int(f),subframe=f-int(f))
 return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def apply(pose):
 set_act(None)
 for n,(q,l) in pose.items():
  pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
 bpy.context.view_layer.update()
def snapshot():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def smooth(x):
 x=min(1,max(0,x));return x*x*(3-2*x)
def mix(a,b,w):
 return {n:((a[n][0] if a[n][0].dot(b[n][0])>=0 else -a[n][0]).slerp(b[n][0],w),a[n][1].lerp(b[n][1],w)) for n in names}
def write(name,poses):
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;set_act(a);prev={}
 for f,pose in enumerate(poses):
  for n,(q,l) in pose.items():
   assert all(math.isfinite(x) for x in q) and abs(q.magnitude-1)<0.002
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
   pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1;set_act(None)
 return a
raw={a.name:[sample(a,f) for f in range(int(a.frame_range[1])+1)] for a in list(bpy.data.actions) if a.use_fake_user}
# The native ready pose carries its blade diagonally across the cuirass, in front of the chest.
apply(raw['Standing'][0])
ref={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
fit=armik.solve_aimed(rig,'R',Vector((-0.27,-0.16,1.10)),G['handle_axis_hand_local'],
                     Vector((0.58,-0.25,0.775)).normalized(),ref,phis=range(-40,41,10),devs=((0,0),))
carry=snapshot()
print('CARRY', {k:fit[k] for k in ('cost','phi','roll','swing','twist')})
for pose in raw['Standing']:
 for n in ('B_R_UpperArm','B_R_Forearm','B_R_Hand'):pose[n]=carry[n]
# Free hand clears the broader kneecap: three degrees of shoulder abduction, with bone lengths unchanged.
for name in ('Standing','Attack'):
 for i,pose in enumerate(raw[name]):
  apply(pose);pb=rig.pose.bones['B_L_UpperArm'];M=rig.matrix_world@pb.matrix;loc=M.translation.copy()
  ch=rig.pose.bones['B_Spine2'];forward=(ch.matrix.to_3x3()@ch.bone.matrix_local.to_3x3().inverted()@Vector((0,-1,0))).normalized()
  M=Matrix.Rotation(math.radians({'Standing':5,'Attack':9,'Hit':15,'Fidget':20}[name]),4,forward)@M;M.translation=loc
  pb.matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update();raw[name][i]=snapshot()
ST=raw['Standing'][0]
# Keep the planted guard under the native-style recoil and alert head scan. Full-body presets crossed the equipment.
for i,pose in enumerate(raw['Hit']):
 adapted={n:(q.copy(),l.copy()) for n,(q,l) in ST.items()}
 for n in ('B_Spine2','B_Neck','B_Head'):adapted[n]=mix(ST,pose,.12 if n=='B_Spine2' else .75)[n]
 raw['Hit'][i]=adapted
for i,pose in enumerate(raw['Fidget']):
 idle=raw['Standing'][i%len(raw['Standing'])]
 adapted={n:(q.copy(),l.copy()) for n,(q,l) in idle.items()}
 for n in ('B_Neck','B_Head'):adapted[n]=mix(ST,pose,.75)[n]
 raw['Fidget'][i]=adapted
# Running keeps the hilt ahead of the moving knees.
prev=None
for i,pose in enumerate(raw['Running']):
 apply(pose);pelvis=(rig.matrix_world@rig.pose.bones['B_Pelvis'].matrix).translation
 for n in ('B_R_UpperArm','B_R_Forearm','B_R_Hand'):rig.pose.bones[n].rotation_quaternion=ST[n][0]
 bpy.context.view_layer.update();ref={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
 fit=armik.solve_aimed(rig,'R',pelvis+Vector((-0.28,-0.36,0.20)),G['handle_axis_hand_local'],Vector((0.58,-0.25,0.775)).normalized(),ref,prev=prev,phis=range(-30,31,10),devs=((0,0),))
 prev=fit;raw['Running'][i]=snapshot()
# Close the Mixamo run's unmatched endpoint over its final four frames, including the fitted weapon arm.
run_end=len(raw['Running'])-1
for i in range(run_end-4,run_end+1):raw['Running'][i]=mix(raw['Running'][i],raw['Running'][0],smooth((i-(run_end-4))/4))
# Locate the descending cut while the blade points towards the victim, then fit the lead to MM8's 1.0 s release.
tips=[];forward=[]
for pose in raw['Attack']:
 apply(pose);M=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix
 c=M@Vector(G['handle_centre_hand_local']);axis=(M.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
 tips.append(np.array(c+axis*0.8));forward.append(-axis.y)
speed=np.linalg.norm(np.diff(tips,axis=0),axis=1)
k=int(np.argmax(np.where(np.array(forward[:-1])>0.5,speed,0)))
impact_raw=(k+0.5)/30;lead=max(1,round((1.0-impact_raw)*30))
attack=[mix(ST,raw['Attack'][0],smooth(i/lead)) for i in range(lead)]+raw['Attack']
attack += [mix(raw['Attack'][-1],ST,smooth(i/8)) for i in range(1,9)]
raw['Attack']=attack
for name,ni,no in [('Hit',3,6),('Fidget',9,9),('Death',6,0)]:
 poses=raw[name]
 raw[name]=[mix(ST,poses[0],smooth(i/ni)) for i in range(ni)]+poses
 if no:raw[name]+=[mix(poses[-1],ST,smooth(i/no)) for i in range(1,no+1)]
assert (len(raw['Hit'])-1)/30<=1.125
# Recompute twist curves after carry and stance changes, without changing skin weights a second time.
def twist(q,axis):
 t=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);return (t+math.pi)%(2*math.pi)-math.pi
for name,poses in raw.items():
 for i,pose in enumerate(poses):
  apply(pose)
  for side in 'LR':
   fb,hb=rig.data.bones[f'B_{side}_Forearm'],rig.data.bones[f'B_{side}_Hand']
   axis=(fb.matrix_local.inverted()@hb.head_local).normalized()
   rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion()
   rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion()
   pose[f'B_{side}_ForearmTwist']=(Quaternion(axis,0.6*twist(rel@rest.inverted(),axis)),pose[f'B_{side}_ForearmTwist'][1])
   ub=rig.data.bones[f'B_{side}_UpperArm'];axis=(ub.matrix_local.inverted()@fb.head_local).normalized()
   pose[f'B_{side}_UpperArmTwist']=(Quaternion(axis,-0.5*twist(pose[ub.name][0],axis)),pose[f'B_{side}_UpperArmTwist'][1])
 write(name,poses)
report={'attack_impact_s':round(lead/30+impact_raw,4),'native_attack_impact_s':1.0,'attack_lead_s':lead/30,
 'roles':{n:{'duration_s':(len(v)-1)/30,'frames':len(v)} for n,v in raw.items()}}
json.dump(report,open(p/'work/clip_timing.json','w'),indent=2)
print('TIMING',json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/polished.blend'))
