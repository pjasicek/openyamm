"""Fit the forward fall to a long skirt: restrained leg flex, with the feet defining the fall's footprint."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/all_timed.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene
def act(a):
 r.animation_data.action=a
 if a:r.animation_data.action_slot=a.slots[0]
st=bpy.data.actions['Standing'];act(st);sc.frame_set(0)
legs=[b.name for b in r.pose.bones if any(t in b.name for t in ('Thigh','Calf','Foot','Toe'))]
base={n:r.pose.bones[n].rotation_quaternion.copy() for n in legs}
anchor=(r.pose.bones['B_L_Foot'].head+r.pose.bones['B_R_Foot'].head)*.5
a=bpy.data.actions['Death'];act(a);N=int(a.frame_range[1]);source=[]
for f in range(N+1):
 sc.frame_set(f);source.append({b.name:b.matrix_basis.copy() for b in r.pose.bones})
o=bpy.data.objects['Body'];parts=[x.value for x in o.data.attributes['piece'].data]
rest={b.name:b.matrix_local.copy() for b in r.data.bones}
def world(n,M):
 b=r.pose.bones[n];base=b.parent.matrix@rest[b.parent.name].inverted()@rest[n] if b.parent else rest[n]
 b.rotation_quaternion=(base.inverted()@M).to_quaternion();bpy.context.view_layer.update()
def aim(n,child,target):
 b=r.pose.bones[n];D=(r.pose.bones[child].head-b.head).rotation_difference(target-b.head)
 M=(D.to_matrix()@b.matrix.to_3x3()).to_4x4();M.translation=b.head;world(n,M)
def fit_grounded_legs():
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh()
 ground=min(v.co.z for v in mm.vertices if parts[v.index] in (0,1,2,3,4,9,11,19));ev.to_mesh_clear()
 turn=Matrix.Rotation(math.radians(82),3,'X')
 for side,shoeids in [('L',(6,14)),('R',(5,15))]:
  th,ca,ft,to=[f'B_{side}_{n}' for n in ('Thigh','Calf','Foot','Toe0')]
  H=r.pose.bones[th].head.copy();footrest=rest[ft].translation
  low=min((turn@(v.co-footrest)).z for v in o.data.vertices if parts[v.index] in shoeids)
  L1=(rest[ca].translation-rest[th].translation).length;L2=(rest[ft].translation-rest[ca].translation).length
  dz=max(-.5,min(.5,ground+.004-low-H.z));D=L1+L2-.004
  W=H+Vector((0,math.sqrt(max(.001,D*D-dz*dz)),dz))
  u=(W-H).normalized();along=(L1*L1-L2*L2+D*D)/(2*D)
  pole=Vector((0,0,1));bend=(pole-u*pole.dot(u)).normalized()
  K=H+u*along+bend*math.sqrt(max(0,L1*L1-along*along))
  aim(th,ca,K);aim(ca,ft,W)
  for n in (ft,to):
   M=(turn@rest[n].to_3x3()).to_4x4();M.translation=r.pose.bones[n].head;world(n,M)
solved=[]
for f,pose in enumerate(source):
 act(None)
 for b in r.pose.bones:b.matrix_basis=pose[b.name]
 bpy.context.view_layer.update()
 for n in legs:
  b=r.pose.bones[n];share=.25 if 'Thigh' in n else (.15 if 'Calf' in n else 0.)
  b.rotation_quaternion=base[n].slerp(b.rotation_quaternion,share)
 bpy.context.view_layer.update()
 # The long dress's corpse has extended legs; the source finishes with raised ankles.
 old={n:r.pose.bones[n].rotation_quaternion.copy() for n in legs}
 t=max(0,min(1,(f-40)/16));w=t*t*(3-2*t)
 if w:
  fit_grounded_legs()
  for n in legs:r.pose.bones[n].rotation_quaternion=old[n].slerp(r.pose.bones[n].rotation_quaternion,w)
  bpy.context.view_layer.update()
 centre=(r.pose.bones['B_L_Foot'].head+r.pose.bones['B_R_Foot'].head)*.5
 delta=Vector((anchor.x-centre.x,anchor.y-centre.y,0))
 pel=r.pose.bones['B_Pelvis']
 basis=pel.parent.matrix@pel.parent.bone.matrix_local.inverted()@pel.bone.matrix_local if pel.parent else pel.bone.matrix_local
 delta=basis.to_3x3().inverted()@delta
 pel.location+=delta;bpy.context.view_layer.update()
 solved.append({n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy()) for n in legs+['B_Pelvis']})
act(a);prev={}
for f,pose in enumerate(solved):
 for n,(q,l) in pose.items():
  if n in prev and q.dot(prev[n])<0:q.negate()
  prev[n]=q.copy();b=r.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
  if n=='B_Pelvis':b.location=l;b.keyframe_insert('location',frame=f)
for lay in a.layers:
 for stp in lay.strips:
  for bag in stp.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/all_draped.blend'))
print('FORWARD FALL',N/30,'seconds; thigh motion 25%, calf 15%; foot-centre anchored')
