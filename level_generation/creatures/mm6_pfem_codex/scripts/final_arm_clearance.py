"""Clear the remaining dress crossings with fixed-length arm rotations."""
import bpy,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene
rest={b.name:b.matrix_local.copy() for b in r.data.bones}
def world(n,M):
 b=r.pose.bones[n];base=b.parent.matrix@rest[b.parent.name].inverted()@rest[n]
 b.rotation_quaternion=(base.inverted()@M).to_quaternion();bpy.context.view_layer.update()
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
for name in ('Walking','Death'):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];poses=[]
 for f in np.arange(0,a.frame_range[1]+.01,.25):
  sc.frame_set(int(f),subframe=float(f%1));poses.append((float(f),{b.name:b.matrix_basis.copy() for b in r.pose.bones}))
 results=[]
 for f,pose in poses:
  r.animation_data.action=None
  for b in r.pose.bones:b.matrix_basis=pose[b.name]
  bpy.context.view_layer.update();names=[]
  if name=='Walking':
   axis=(r.pose.bones['B_Pelvis'].matrix@rest['B_Pelvis'].inverted()).to_3x3()@Vector((0,1,0))
   for side,sign in [('L',-1),('R',1)]:
    n=f'B_{side}_UpperArm';b=r.pose.bones[n];M=Quaternion(axis,math.radians(6)*sign).to_matrix().to_4x4()@b.matrix;M.translation=b.head
    world(n,M);names.append(n)
  else:
   pulse=math.sin(math.pi*min(f/6,1))**2
   for side,sign in [('L',1),('R',-1)]:names+=arm(side,Vector((sign*.045*pulse,-.085*pulse,0)))
  results.append((f,{n:r.pose.bones[n].rotation_quaternion.copy() for n in names}))
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];prev={}
 for f,pose in results:
  for n,Q in pose.items():
   if n in prev and Q.dot(prev[n])<0:Q.negate()
   prev[n]=Q.copy();b=r.pose.bones[n];b.rotation_quaternion=Q;b.keyframe_insert('rotation_quaternion',frame=f)
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured_uv.blend'))
