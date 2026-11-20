"""Native upright guard, brief hit, and continuous entry/recovery for the selected source clips."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_fingers.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;names=list(rig.pose.bones.keys())
def setact(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 setact(a);sc.frame_set(int(f),subframe=f%1)
 return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def smooth(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def blend(a,b,t):return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t)) for n in names}
def write(name,poses):
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;setact(a);prev={}
 for f,pose in enumerate(poses):
  for n,(q,l) in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
   pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1;setact(None)
raw={a.name:[sample(a,f) for f in range(int(a.frame_range[1])+1)] for a in bpy.data.actions if a.use_fake_user}
base={n:raw['Standing'][0][n][0].copy() for n in ('B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head')}
for name in ('Standing','Fidget','Walking'):
 poses=raw[name]
 for frame,pose in enumerate(poses):
  for n in names:
   if name!='Walking' and (n=='B_Pelvis' or any(k in n for k in ('Thigh','Calf','Foot','Toe0'))):
    q,l=pose[n];pose[n]=(Quaternion().slerp(q,.12),Vector((0,0,0)))
  for n in base:
   q,l=pose[n];corrected=q@base[n].inverted();pose[n]=(Quaternion().slerp(corrected,.35) if name=='Walking' else corrected,l)
  if name=='Walking':
   for n in ('B_Pelvis','B_L_Clavicle','B_R_Clavicle'):
    q,l=pose[n];neutral=Quaternion() if n=='B_Pelvis' else raw['Standing'][0][n][0];pose[n]=(neutral.slerp(q,.3),l)
  # Retain the source's tiny breath; the pelvis is otherwise in the native neutral stance.
  if name!='Walking':
   q,l=pose['B_Pelvis'];pose['B_Pelvis']=(q,Vector((0,math.sin(math.tau*frame/max(1,len(poses)-1))*.003,0)))
 write(name,poses)
home=sample(bpy.data.actions['Standing'],0)
for name in ('Attack','Hit','Death'):
 poses=raw[name]
 if name=='Hit':poses=poses[:16]
 result=[]
 for f,pose in enumerate(poses):
  if name=='Attack':
   for n in ('B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'):
    pose[n]=(home[n][0].slerp(pose[n][0],.25),pose[n][1])
  if name in ('Attack','Death'):
   for n in ('B_L_Clavicle','B_R_Clavicle'):
    pose[n]=(home[n][0].slerp(pose[n][0],.25),pose[n][1])
  if name=='Hit':
   for n in names:
    if any(k in n for k in ('Clavicle','UpperArm','Forearm','Hand','Finger')):
     pose[n]=(home[n][0].slerp(pose[n][0],.35),home[n][1])
  enter=6 if name!='Hit' else 3;leave=6 if name!='Hit' else 5
  weight=min(smooth(f/enter),smooth((len(poses)-1-f)/leave)) if name!='Death' else smooth(f/enter)
  result.append(blend(home,pose,weight))
 write(name,result)
setact(None)
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
json.dump({'Standing':'12 percent source lower-body rotation; rest stance and subtle breathing','Hit':.5,'Attack':(len(raw['Attack'])-1)/30,'Death':(len(raw['Death'])-1)/30,'Fidget':(len(raw['Fidget'])-1)/30,'blend_in_seconds':.2,'blend_out_seconds':.2},open(p/'work/posture_timing.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_stance.blend'))
