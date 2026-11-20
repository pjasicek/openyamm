"""Keep the chosen upper-body cut, fit its planted stance, carry the sword and articulate plates."""
import bpy,sys,json,runpy,math,os
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
import numpy as np
p=Path(__file__).resolve().parents[1];s=p/'scripts';w=p/'work';sys.path.insert(0,str(s));import armik
bpy.ops.wm.open_mainfile(filepath=str(w/'rig_v5.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
names=[b.name for b in rig.data.bones];legs=[n for n in names if any(x in n for x in ['Thigh','Calf','Foot','Toe'])]
def act(a):
 rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 act(a);sc.frame_set(int(f),subframe=f%1);return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def apply(pose):
 act(None)
 for n,(q,l) in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
def write(name,poses):
 bpy.data.actions.remove(bpy.data.actions[name]);a=bpy.data.actions.new(name);a.use_fake_user=True;act(a);prev={}
 for f,pose in enumerate(poses):
  for n,(q,l) in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l;b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
st=sample(bpy.data.actions['Standing'],0)
for name in ['Attack','Hit']:
 a=bpy.data.actions[name];poses=[]
 for f in range(int(a.frame_range[1])+1):
  pose=sample(a,f);world={n:rig.pose.bones[n].matrix.to_3x3().copy() for n in names};pose['B_Pelvis']=st['B_Pelvis']
  for n in legs:pose[n]=st[n]
  apply(pose)
  for n in names:
   if n in legs or n=='B_Pelvis':continue
   m=world[n].to_4x4();m.translation=rig.pose.bones[n].head;rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
  poses.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names})
 write(name,poses)
# The unarmed right hand stays comfortably open; the fitted left fist stays fixed.
for a in bpy.data.actions:
 if not a.use_fake_user:continue
 act(a)
 for b in rig.pose.bones:
  if not b.name.startswith('B_R_Finger'):continue
  for f in range(int(a.frame_range[1])+1):b.rotation_quaternion=Quaternion();b.keyframe_insert('rotation_quaternion',frame=f)
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(w/'motion_planted.blend'))
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(s/n),run_name='__main__')
os.environ['RUN_STRIDE']='1.6';run('run_fit.py',w/'motion_planted.blend',w/'motion_runfit.blend')
run('author_carry.py',w/'motion_runfit.blend',w/'motion_carry.blend','Standing:0.12','Walking:0.20','Running:0.30','Fidget:0.08')
bpy.ops.wm.open_mainfile(filepath=str(w/'motion_carry.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
# Blend guard transitions without changing the source cut duration or native hit duration.
st=sample(bpy.data.actions['Standing'],0)
for name,lead,tail in [('Attack',4,5),('Hit',3,5),('Fidget',8,8),('Death',7,0)]:
 a=bpy.data.actions[name];N=int(a.frame_range[1]);poses=[sample(a,f) for f in range(N+1)]
 for f,pose in enumerate(poses):
  t=min(1,f/lead,(N-f)/tail if tail else 1);t=t*t*(3-2*t)
  for n,(q,l) in list(pose.items()):
   sq,sl=st[n];pose[n]=((sq if sq.dot(q)>=0 else -sq).slerp(q,t),sl.lerp(l,t))
  if name=='Death':
   q,l=pose['B_Pelvis'];R=rig.data.bones['B_Pelvis'].matrix_local.to_3x3();delta=R@(l-st['B_Pelvis'][1]);delta.x*=.45;delta.y*=.45;pose['B_Pelvis']=(q,st['B_Pelvis'][1]+R.inverted()@delta)
 write(name,poses)
act(None)
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for sd in 'LR':
 u=rig.data.edit_bones[f'B_{sd}_UpperArm'];b=rig.data.edit_bones.new(f'B_{sd}_Pauldron');b.head=u.head;b.tail=u.tail;b.roll=u.roll;b.parent=rig.data.edit_bones[f'B_{sd}_Clavicle']
bpy.ops.object.mode_set(mode='OBJECT')
for sd,pid in [('L',18),('R',17)]:
 vg=body.vertex_groups.new(name=f'B_{sd}_Pauldron');ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value==pid]
 for g in body.vertex_groups:g.remove(ids)
 vg.add(ids,1,'REPLACE')
for pid in [12,14]:
 ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value==pid]
 for g in body.vertex_groups:g.remove(ids)
 body.vertex_groups['B_Spine2'].add(ids,1,'REPLACE')
for a in bpy.data.actions:
 if not a.use_fake_user:continue
 act(a)
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f)
  for sd in 'LR':
   ua,fa,cl=[rig.data.bones[f'B_{sd}_{b}'] for b in ['UpperArm','Forearm','Clavicle']];D=rig.pose.bones[cl.name].matrix.to_3x3()@cl.matrix_local.to_3x3().inverted()
   original=D@(fa.head_local-ua.head_local);current=rig.pose.bones[fa.name].head-rig.pose.bones[ua.name].head
   R=original.rotation_difference(current).to_matrix()@D@ua.matrix_local.to_3x3();pb=rig.pose.bones[f'B_{sd}_Pauldron'];m=R.to_4x4();m.translation=pb.head;pb.matrix=m;pb.rotation_mode='QUATERNION';pb.keyframe_insert('rotation_quaternion',frame=f)
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(w/'motion_armour.blend'))
# Recompute twist bones after fitting the carrying arm.
run('twist_bones.py',w/'motion_armour.blend',w/'motion_ready.blend')
for view in ['front','left','three_quarter']:run('clip_sheet.py',w/'motion_ready.blend',p/'review/pilot2'/view,view,7,'Standing','Walking','Running','Attack','Hit','Fidget','Death')
