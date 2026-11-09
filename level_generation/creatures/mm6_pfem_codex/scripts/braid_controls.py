"""Two fitted braid controls replace two unused toe end bones (128 total)."""
import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.objects.active=r
bpy.ops.object.mode_set(mode='EDIT')
for n in ('B_L_Toe0','B_R_Toe0'):
 assert not any(any(o.vertex_groups[g.group].name==n and g.weight>1e-6 for g in v.groups) for v in o.data.vertices)
 r.data.edit_bones.remove(r.data.edit_bones[n])
for name,h,t,parent in [('B_Braid',(0,.080,1.47),(0,.083,1.39),'B_Head'),('B_BraidTip',(0,.083,1.39),(0,.086,1.31),'B_Braid')]:
 b=r.data.edit_bones.new(name);b.head=h;b.tail=t;b.parent=r.data.edit_bones[parent];b.use_connect=name=='B_BraidTip';b.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
pv=[x.value for x in o.data.attributes['piece'].data]
for n in ('B_Braid','B_BraidTip'):
 if n not in o.vertex_groups:o.vertex_groups.new(name=n)
for v in o.data.vertices:
 if pv[v.index]!=19:continue
 t=max(0,min(1,(1.402-v.co.z)/.025));t=t*t*(3-2*t)
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 if t<1:o.vertex_groups['B_Braid'].add([v.index],1-t,'REPLACE')
 if t>0:o.vertex_groups['B_BraidTip'].add([v.index],t,'REPLACE')
rest={b.name:b.matrix_local.copy() for b in r.data.bones}
def world(n,M):
 b=r.pose.bones[n];base=b.parent.matrix@rest[b.parent.name].inverted()@rest[n]
 b.rotation_quaternion=(base.inverted()@M).to_quaternion();bpy.context.view_layer.update()
def aim(n,point):
 b=r.pose.bones[n];D=(b.tail-b.head).normalized().rotation_difference((point-b.head).normalized())
 M=(D.to_matrix()@b.matrix.to_3x3()).to_4x4();M.translation=b.head;world(n,M)
for name in ('Standing','Walking','Hit','Death','Fidget'):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 data=[];previous={}
 for f in np.arange(0,a.frame_range[1]+.01,.25):
  sc.frame_set(int(f),subframe=float(f%1))
  for n in ('B_Braid','B_BraidTip'):r.pose.bones[n].matrix_basis.identity()
  bpy.context.view_layer.update()
  S=r.pose.bones['B_Braid'].head.copy();M=r.pose.bones['B_Spine2'].matrix@rest['B_Spine2'].inverted()
  T=M@Vector((0,.116,1.31));back=M.to_3x3()@Vector((0,1,0))
  L=(rest['B_BraidTip'].translation-rest['B_Braid'].translation).length
  d=min((T-S).length,2*L-.0005);u=(T-S).normalized();T=S+u*d
  bend=(back-u*back.dot(u)).normalized()
  E=S+u*(d/2)+bend*math.sqrt(max(0,L*L-d*d/4))
  aim('B_Braid',E);aim('B_BraidTip',T)
  data.append((float(f),{n:r.pose.bones[n].rotation_quaternion.copy() for n in ('B_Braid','B_BraidTip')}))
 for f,pose in data:
  for n,Q in pose.items():
   if n in previous and Q.dot(previous[n])<0:Q.negate()
   previous[n]=Q.copy();b=r.pose.bones[n];b.rotation_quaternion=Q;b.keyframe_insert('rotation_quaternion',frame=f)
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     if 'B_Braid' in fc.data_path:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
print('Braid controls',len(r.data.bones))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured_uv.blend'))
