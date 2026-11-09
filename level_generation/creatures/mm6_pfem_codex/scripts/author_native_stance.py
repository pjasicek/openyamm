"""Native clasped idle and quiet glance; fixed-length arm IK over the selected upright source stance."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/grounded_weighted.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
def setact(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def world(n,M):
 b=rig.pose.bones[n];base=b.parent.matrix@rest[b.parent.name].inverted()@rest[n] if b.parent else rest[n]
 local=base.inverted()@M;b.rotation_mode='QUATERNION';b.rotation_quaternion=local.to_quaternion()
 # Only rotations change on fixed-length limbs.
 if n=='B_Pelvis':b.location=local.translation
 bpy.context.view_layer.update()
def align(n,child,target):
 b=rig.pose.bones[n];old=(rig.pose.bones[child].head-b.head).normalized()
 rot=old.rotation_difference((target-b.head).normalized())
 M=(rot.to_matrix()@b.matrix.to_3x3()).to_4x4();M.translation=b.head;world(n,M)
def key(n,f):
 b=rig.pose.bones[n];b.keyframe_insert('rotation_quaternion',frame=f)
 if n=='B_Pelvis':b.keyframe_insert('location',frame=f)
def smooth(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def basis(f,t):
 f=f.normalized();t=(t-f*t.dot(f)).normalized()
 return Matrix((f,t,f.cross(t))).transposed()
a=bpy.data.actions['Standing'];setact(a)
poses=[]
for f in range(61):
 scene.frame_set(f);poses.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
FJ=json.load(open(p/'work/finger_joints.json'))
for f in range(61):
 scene.frame_set(f)
 for b in rig.pose.bones:b.matrix_basis=poses[f][b.name]
 bpy.context.view_layer.update()
 pelvis=rig.pose.bones['B_Pelvis'].head.copy()
 dz=pelvis.z-.99917
 for side in 'RL':
  sign=1 if side=='L' else -1
  upper,fore,hand=[f'B_{side}_{n}' for n in ('UpperArm','Forearm','Hand')]
  S=rig.pose.bones[upper].head.copy()
  W=Vector((sign*.038,-.192 if side=='L' else -.240,1.010 if side=='L' else .995))
  W.z+=dz
  l1=(rest[fore].translation-rest[upper].translation).length;l2=(rest[hand].translation-rest[fore].translation).length
  axis=(W-S).normalized();d=(W-S).length
  assert abs(l1-l2)<d<l1+l2,(side,d,l1,l2)
  along=(l1*l1-l2*l2+d*d)/(2*d)
  pole=Vector((sign*.32,-.06,1.08+dz))-S
  bend=(pole-axis*pole.dot(axis)).normalized()
  E=S+axis*along+bend*math.sqrt(max(0,l1*l1-along*along))
  align(upper,fore,E);align(fore,hand,W)
  wr=rest[hand].translation
  f0=Vector(FJ[side][f'B_{side}_Finger2'])-wr
  t0=Vector(FJ[side][f'B_{side}_Finger1'])-Vector(FJ[side][f'B_{side}_Finger4'])
  fd=Vector((-sign*.30,-.03,-.954));td=Vector((-sign*.954,-.08,.30))
  D=basis(fd,td)@basis(f0,t0).inverted()
  M=(D@rest[hand].to_3x3()).to_4x4();M.translation=rig.pose.bones[hand].head
  world(hand,M)
  for n in (upper,fore,hand):key(n,f)
# The fidget shares the clasped idle, with a restrained glance each way.
st=bpy.data.actions['Standing'];frames=[]
for f in range(91):
 setact(st);sf=f*60/90;scene.frame_set(int(sf),subframe=sf%1)
 pose={b.name:b.matrix_basis.copy() for b in rig.pose.bones};frames.append(pose)
act=bpy.data.actions.new('Fidget');act.use_fake_user=True;setact(act)
anchors=[(0,0),(.65,-12),(1.15,-12),(1.95,10),(2.45,10),(3.,0)]
for f,pose in enumerate(frames):
 scene.frame_set(f)
 for b in rig.pose.bones:b.matrix_basis=pose[b.name]
 bpy.context.view_layer.update();t=f/30
 for (a0,y0),(a1,y1) in zip(anchors,anchors[1:]):
  if a0<=t<=a1:yaw=math.radians(y0+(y1-y0)*smooth((t-a0)/(a1-a0)));break
 for n,share in [('B_Neck',.35),('B_Head',.65)]:
  M=rig.pose.bones[n].matrix.copy();rot=Matrix.Rotation(yaw*share,3,'Z')@M.to_3x3()
  N=rot.to_4x4();N.translation=M.translation;world(n,N)
 for b in rig.pose.bones:key(b.name,f)
act.use_frame_range=True;act.frame_start=0;act.frame_end=90
for a in bpy.data.actions:
 for l in a.layers:
  for s in l.strips:
   for cb in s.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
setact(st);scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/native_base.blend'))
