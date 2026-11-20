"""Small fixed-length pose corrections for measured return-path hand contacts and the prone head/arm contact."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/all_draped.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene
rest={b.name:b.matrix_local.copy() for b in r.data.bones}
def sm(v):
 v=max(0,min(1,v));return v*v*(3-2*v)
def setact(a):
 r.animation_data.action=a
 if a:r.animation_data.action_slot=a.slots[0]
def world(n,M):
 b=r.pose.bones[n];base=b.parent.matrix@rest[b.parent.name].inverted()@rest[n] if b.parent else rest[n]
 b.rotation_mode='QUATERNION';b.rotation_quaternion=(base.inverted()@M).to_quaternion();bpy.context.view_layer.update()
def aim(n,child,target):
 b=r.pose.bones[n];old=(r.pose.bones[child].head-b.head).normalized()
 D=old.rotation_difference((target-b.head).normalized());M=(D.to_matrix()@b.matrix.to_3x3()).to_4x4();M.translation=b.head;world(n,M)
def arm(side,off):
 upper,fore,hand=[f'B_{side}_{n}' for n in ('UpperArm','Forearm','Hand')]
 S=r.pose.bones[upper].head.copy();E=r.pose.bones[fore].head.copy();W=r.pose.bones[hand].head.copy()
 H=r.pose.bones[hand].matrix.copy();W+=off
 a=(rest[fore].translation-rest[upper].translation).length;b=(rest[hand].translation-rest[fore].translation).length
 d=min((W-S).length,a+b-.001);u=(W-S).normalized();W=S+u*d
 along=(a*a-b*b+d*d)/(2*d);pole=E-S
 bend=(pole-u*pole.dot(u)).normalized();NE=S+u*along+bend*math.sqrt(max(0,a*a-along*along))
 aim(upper,fore,NE);aim(fore,hand,W);H.translation=r.pose.bones[hand].head;world(hand,H)
 return [upper,fore,hand]
report={}
for name in ('Hit','Death'):
 a=bpy.data.actions[name];setact(a);f0,f1=map(int,a.frame_range);snap=[]
 for f in range(f0,f1+1):
  sc.frame_set(f);snap.append({b.name:b.matrix_basis.copy() for b in r.pose.bones})
 keys=[]
 for f,pose in enumerate(snap):
  setact(None);sc.frame_set(f)
  for b in r.pose.bones:b.matrix_basis=pose[b.name]
  bpy.context.view_layer.update();t=f/30;changed=[]
  if name=='Hit':
   pulse=sm((t-.30)/.075)*(1-sm((t-.41)/.09))
   for side in 'RL':changed+=arm(side,Vector((0,(-1 if side=='R' else 1)*.07*pulse,0)))
  else:
   pulse=math.sin(math.pi*min(t/.20,1))**2
   for side in 'RL':changed+=arm(side,Vector((0,(-1 if side=='R' else 1)*.045*pulse,0)))
  keys.append({n:r.pose.bones[n].rotation_quaternion.copy() for n in changed})
 setact(a)
 prev={}
 for f,k in enumerate(keys):
  for n,Q in k.items():
   if n in prev and Q.dot(prev[n])<0:Q.negate()
   prev[n]=Q.copy();b=r.pose.bones[n];b.rotation_quaternion=Q;b.keyframe_insert('rotation_quaternion',frame=f)
 for l in a.layers:
  for s in l.strips:
   for cb in s.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[name]=len(keys)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/all_corrected.blend'))
print('CONTACT CORRECTIONS',report)
