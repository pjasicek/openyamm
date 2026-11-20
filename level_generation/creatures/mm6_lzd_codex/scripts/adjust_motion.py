"""Native upright posture, 20% planted stance, source release and source-relative bow alignment."""
import bpy,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v6_run.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones]
def setact(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 setact(a);scene.frame_set(int(f),subframe=float(f%1));return{n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names}
def apply(p):
 setact(None)
 for n,(q,l)in p.items():pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
 bpy.context.view_layer.update()
def getpose():return{n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names}
def turn(n,axis,ang):
 pb=rig.pose.bones[n];M=pb.matrix.copy();t=M.translation.copy();M=Matrix.Rotation(ang,4,axis)@M;M.translation=t;pb.matrix=M;bpy.context.view_layer.update()
def aim(n,child,target):
 pb=rig.pose.bones[n];M=pb.matrix.copy();cur=rig.pose.bones[child].head-pb.head;want=target-pb.head;q=cur.rotation_difference(want);t=M.translation.copy();M=q.to_matrix().to_4x4()@M;M.translation=t;pb.matrix=M;bpy.context.view_layer.update()
def leg_ik(sd,T,rotation):
 th,ca,ft=[f'B_{sd}_{n}'for n in ('Thigh','Calf','Foot')];H=rig.pose.bones[th].head.copy();K=rig.pose.bones[ca].head.copy();A=rig.pose.bones[ft].head.copy();a=(K-H).length;b=(A-K).length;u=(T-H).normalized();d=min((T-H).length,(a+b)*.9999);v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=np.clip((a*a+d*d-b*b)/(2*a*d),-1,1);Kn=H+a*(u*c+v*math.sqrt(1-c*c));aim(th,ca,Kn);aim(ca,ft,T);m=rotation.to_matrix().to_4x4();m.translation=rig.pose.bones[ft].head;rig.pose.bones[ft].matrix=m;bpy.context.view_layer.update()
def write(n,poses):
 old=bpy.data.actions.get(n)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(n);a.use_fake_user=True;setact(a)
 for f,p in enumerate(poses):
  for bn,(q,l)in p.items():
   pb=rig.pose.bones[bn];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1;return a
st=bpy.data.actions['Standing'];home=sample(st,0);apply(home);foot={sd:(rig.pose.bones[f'B_{sd}_Foot'].head.copy(),rig.pose.bones[f'B_{sd}_Foot'].matrix.to_quaternion())for sd in 'LR'}
G=json.loads((P/'work/grip_pose.json').read_text());axis=Vector(G['handle_axis_hand_local']);report={}
for nm in ['Standing','Walking','Running','Attack','Hit','Death']:
 act=bpy.data.actions[nm];N=int(act.frame_range[1]);poses=[]
 for f in range(N+1):
  pose=sample(act,f)
  if nm=='Running':
   walk=sample(bpy.data.actions['Walking'],f/N*24)
   for bn in names:
    if any(k in bn for k in ('Clavicle','UpperArm','Forearm','Hand','Finger')):pose[bn]=walk[bn]
  apply(pose);spworld=rig.pose.bones['B_Spine'].matrix.to_quaternion()
  if nm in ('Attack','Hit'):
   pb=rig.pose.bones['B_Pelvis'];pb.rotation_quaternion=home['B_Pelvis'][0].slerp(pose['B_Pelvis'][0],.2);pb.location=home['B_Pelvis'][1].lerp(pose['B_Pelvis'][1],.2);bpy.context.view_layer.update()
   for sd in 'LR':leg_ik(sd,*foot[sd])
   pb=rig.pose.bones['B_Spine'];M=spworld.to_matrix().to_4x4();M.translation=pb.head;pb.matrix=M;bpy.context.view_layer.update()
  # Relax the source's chest-resting right hand clear of the tunic.
  turn('B_R_UpperArm','X',math.radians(-12))
  if nm=='Attack':
   # At the held draw the bow's long axis must be vertical, with the fingers still around the same handle.
   u=np.clip((f-5)/5,0,1)*np.clip((21-f)/5,0,1);u=u*u*(3-2*u)
   pb=rig.pose.bones['B_L_Hand'];a=(pb.matrix.to_3x3()@axis).normalized();target=Vector((0,0,1));q=a.rotation_difference(target);M=pb.matrix.copy();t=M.translation.copy();M=Quaternion().slerp(q,float(u)).to_matrix().to_4x4()@M;M.translation=t;pb.matrix=M;bpy.context.view_layer.update()
  if nm not in ('Death',):
   # Reptilian gaze is level in the source frames; keep the head upright over the turned torso.
   pb=rig.pose.bones['B_Head'];m=rig.data.bones['B_Head'].matrix_local.copy();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
  poses.append(getpose())
 report[nm]={'frames':len(poses)};write(nm,poses)
# The measured source release is between frames 14 and 15 (0.4667 s), before the right-hand recoil.
# Add a ready lead-in so the release lands near the native 0.75 s wind-up without accelerating the draw.
at=bpy.data.actions['Attack'];raw=[sample(at,f)for f in range(25)];start=sample(bpy.data.actions['Standing'],0);lead=9
poses=[]
for i in range(lead):
 t=i/lead;t=t*t*(3-2*t);poses.append({n:(start[n][0].slerp(raw[0][n][0],t),start[n][1].lerp(raw[0][n][1],t))for n in names})
poses+=raw;write('Attack',poses)
# Native fidget is a modest scan; the bow stays held and the stance stays planted.
poses=[]
for f in range(31):
 apply(sample(bpy.data.actions['Standing'],f));turn('B_Head','Z',math.radians(12)*math.sin(2*math.pi*f/30));poses.append(getpose())
write('Fidget',poses);death=bpy.data.actions['Death'];last=sample(death,death.frame_range[1]);write('Dead',[last for _ in range(31)])
report['release']={'source_frame':14,'lead_frames':lead,'impact_seconds':(lead+14)/30,'native_action_seconds':.75}
(P/'work/clip_timing.json').write_text(json.dumps(report,indent=2));setact(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_motion.blend'))
