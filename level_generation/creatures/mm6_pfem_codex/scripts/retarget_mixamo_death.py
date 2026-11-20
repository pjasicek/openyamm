"""Convert the local Mixamo forward death into the fitted B_* source frames, keeping world-space motion."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilots_raw.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
names=[b.name for b in r.data.bones];S=json.load(open(p/'work/source_rest.json'))
M={'B_Pelvis':'Hips','B_Spine':'Spine','B_Spine1':'Spine1','B_Spine2':'Spine2','B_Neck':'Neck','B_Head':'Head'}
for side,long in [('L','Left'),('R','Right')]:
 for short,b in [('Clavicle','Shoulder'),('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Thigh','UpLeg'),('Calf','Leg'),('Foot','Foot'),('Toe0','ToeBase')]:M[f'B_{side}_{short}']=long+b
 for n in names:
  if not n.startswith(f'B_{side}_Finger'):continue
  tail=n.split('Finger')[1];digit=int(tail[0]);finger=['Thumb','Index','Middle','Ring','Pinky'][digit]
  joint=int(tail.split('.')[1]) if '.' in tail else (int(tail[1:]) if len(tail)>1 else 0)
  M[n]=f'{long}Hand{finger}{joint+1}'
before=set(bpy.data.objects);actbefore=set(bpy.data.actions);sc.render.fps=30
bpy.ops.import_scene.fbx(filepath='/home/pjasicek/Downloads/mixamo_library/Standing Death Forward 02.fbx')
sr=next(o for o in set(bpy.data.objects)-before if o.type=='ARMATURE');a=sr.animation_data.action
lookup={b.name.split(':')[-1]:b.name for b in sr.data.bones};M={n:lookup[m] for n,m in M.items()}
W=sr.matrix_world.copy();rest={n:(W@sr.data.bones[m].matrix_local).to_3x3().normalized() for n,m in M.items()}
heads={n:W@sr.data.bones[m].head_local for n,m in M.items()}
Q={}
def basis(f,t):
 f=f.normalized();t=(t-f*t.dot(f)).normalized();return Matrix((f,t,f.cross(t))).transposed()
for n in names:
 child=S[n]['child'];par=S[n]['parent']
 if child in heads and S[n]['seg']:
  Q[n]=Vector(S[n]['seg']).rotation_difference(heads[child]-heads[n]).to_matrix()
 else:Q[n]=Q.get(par,Matrix.Identity(3))
 if n.endswith('_Hand'):
  side=n.split('_')[1];f1,f2,f4=[f'B_{side}_Finger{i}' for i in (1,2,4)]
  canon=basis(Vector(S[f2]['head'])-Vector(S[n]['head']),Vector(S[f1]['head'])-Vector(S[f4]['head']))
  mix=basis(heads[f2]-heads[n],heads[f1]-heads[f4]);Q[n]=mix@canon.inverted()
 if n=='B_Pelvis':Q[n]=Matrix.Identity(3)
fps=sc.render.fps/sc.render.fps_base;f0,f1=a.frame_range;N=round((f1-f0)/fps*30)
k=r.data.bones['B_Pelvis'].head_local.z/heads['B_Pelvis'].z
poses=[];start=None
for f in range(N+1):
 sf=f0+f/30*fps;sc.frame_set(int(sf),subframe=float(sf%1))
 for b in r.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update()
 for n in names:
  D=(W@sr.pose.bones[M[n]].matrix).to_3x3().normalized()@rest[n].inverted()
  R=D@Q[n]@Matrix(S[n]['rot']);b=r.pose.bones[n];mat=R.to_4x4()
  mat.translation=b.head
  if n=='B_Pelvis':
   loc=(W@sr.pose.bones[M[n]].matrix).translation*k
   if start is None:start=loc.copy()
   mat.translation=loc-Vector((start.x,start.y,0))
  base=b.parent.matrix@b.parent.bone.matrix_local.inverted()@b.bone.matrix_local if b.parent else b.bone.matrix_local
  local=base.inverted()@mat;b.rotation_mode='QUATERNION';b.rotation_quaternion=local.to_quaternion()
  if n=='B_Pelvis':b.location=local.translation
  bpy.context.view_layer.update()
 poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in r.pose.bones})
for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
for a in set(bpy.data.actions)-actbefore:bpy.data.actions.remove(a)
if 'Death' in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions['Death'])
a=bpy.data.actions.new('Death');a.use_fake_user=True;r.animation_data.action=a;prev={}
for f,pose in enumerate(poses):
 for n,(q,l) in pose.items():
  if n in prev and q.dot(prev[n])<0:q.negate()
  prev[n]=q.copy();b=r.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l
  b.keyframe_insert('rotation_quaternion',frame=f)
  if n=='B_Pelvis':b.keyframe_insert('location',frame=f)
a.use_frame_range=True;a.frame_start=0;a.frame_end=N;sc.render.fps=30
for lay in a.layers:
 for st in lay.strips:
  for cb in st.channelbags:
   for fc in cb.fcurves:
    for key in fc.keyframe_points:key.interpolation='LINEAR'
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilots_raw.blend'))
(p/'work/mixamo_death_retarget.json').write_text(json.dumps({'source':'/home/pjasicek/Downloads/mixamo_library/Standing Death Forward 02.fbx','frames':N+1,'duration':N/30,'pelvis_height_scale':k,'map':M},indent=2))
print('MIXAMO RETARGET',N+1,'frames',N/30,'seconds')
