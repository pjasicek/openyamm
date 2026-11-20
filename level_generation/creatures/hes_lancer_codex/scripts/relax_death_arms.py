"""Let the released arms settle into the existing corpse pose; retain the source fall and weapon path."""
import bpy,sys,math
import numpy as np
from mathutils import Vector,Quaternion
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));import armik
src,out,family,weapon=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=src)
r=bpy.data.objects['Rig'];sc=bpy.context.scene;r.animation_data_create();names=[f'B_{s}_{n}' for s in 'LR' for n in ('UpperArm','Forearm','Hand')]
dead=bpy.data.actions[family+'_Dead'];r.animation_data.action=dead;r.animation_data.action_slot=dead.slots[0];sc.frame_set(0);target={n:r.pose.bones[n].matrix_basis.copy() for n in names}
a=bpy.data.actions[family+'_Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0);start={n:r.pose.bones[n].matrix_basis.copy() for n in names};keys=[]
for frame in range(int(a.frame_range[1])+1):
 sc.frame_set(frame);gun=armik.W(r,weapon).copy();k=min(1,frame/15);k=k*k*(3-2*k)
 for n in names:
  b=r.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=start[n].to_quaternion().slerp(target[n].to_quaternion(),k);b.location=start[n].translation.lerp(target[n].translation,k)
 bpy.context.view_layer.update();armik.set_world(r,weapon,gun);assert (armik.W(r,weapon).translation-gun.translation).length<1e-5
 keys.append({n:r.pose.bones[n].matrix_basis.copy() for n in [*names,weapon]})
previous={}
for frame,pose in enumerate(keys):
 for n,m in pose.items():
  b=r.pose.bones[n];q=m.to_quaternion()
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame)
# Keep the free claws and bracers above the floor throughout the retained torso fall.
body=bpy.data.objects['Body'];groups=[g.name for g in body.vertex_groups]
masks={s:np.array([sum(g.weight for g in v.groups if groups[g.group].startswith('B_'+s+'_') and any(t in groups[g.group] for t in ('UpperArm','Forearm','Hand','Finger')))>.25 for v in body.data.vertices]) for s in 'LR'}
frames=range(int(a.frame_range[1])+1)
def coords(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([o.matrix_world@p.co for p in m.vertices]);e.to_mesh_clear();return v
for iteration in range(4):
 offsets={s:[] for s in 'LR'}
 for frame in frames:
  sc.frame_set(frame);v=coords(body)
  for side in 'LR':
   low=float(v[masks[side],2].min())
   for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith('Arm_') and o.get('bone')==f'B_{side}_Forearm':low=min(low,float(coords(o)[:,2].min()))
   offsets[side].append(max(0,.005-low))
 if iteration==0:floor_weight=np.clip(np.array(offsets['L'])/.025,0,1)
 if max(max(x) for x in offsets.values())<.0005:break
 for side in 'LR':
  raw=np.array(offsets[side]);offsets[side]=np.maximum(raw,np.convolve(np.pad(raw,2,mode='edge'),np.array([1,2,3,2,1])/9,mode='valid'))
 keys=[]
 for frame in frames:
  sc.frame_set(frame);gun=armik.W(r,weapon).copy()
  for side in 'LR':
   d=float(offsets[side][frame])
   if d<.0001:continue
   h=armik.W(r,f'B_{side}_Hand').copy();elbow=armik.W(r,f'B_{side}_Forearm').translation.copy()
   armik.solve(r,side,h.translation+Vector((0,0,d)),elbow+Vector((0,0,d)),h.to_3x3().normalized())
   r.pose.bones[f'B_{side}_Hand'].rotation_quaternion=target[f'B_{side}_Hand'].to_quaternion()
  bpy.context.view_layer.update();armik.set_world(r,weapon,gun);keys.append({n:r.pose.bones[n].matrix_basis.copy() for n in [*names,weapon]})
 previous={}
 for frame,pose in enumerate(keys):
  for n,m in pose.items():
   b=r.pose.bones[n];q=m.to_quaternion()
   if n in previous and q.dot(previous[n])<0:q=-q
   previous[n]=q.copy();b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame)
 print('FREE_ARM_FLOOR',iteration,{s:round(max(offsets[s]),4) for s in 'LR'},flush=True)

# The planted left hand needs an outward elbow plane, not a twist through the shoulder skin.
envelope=np.array([max(floor_weight[max(0,i-8):min(len(floor_weight),i+9)]) for i in range(len(floor_weight))]);kernel=np.exp(-.5*(np.arange(-8,9)/4)**2);kernel/=kernel.sum();envelope=np.convolve(np.pad(envelope,8),kernel,mode='valid')
keys=[]
for frame in frames:
 sc.frame_set(frame);h=armik.W(r,'B_L_Hand').copy();u=armik.W(r,'B_L_UpperArm').translation.copy();elbow=armik.W(r,'B_L_Forearm').translation.copy();pole=u+Quaternion((h.translation-u).normalized(),math.radians(-90*float(envelope[frame])))@(elbow-u)
 armik.solve(r,'L',h.translation,pole,h.to_3x3().normalized());assert (armik.W(r,'B_L_Hand').translation-h.translation).length<1e-5
 keys.append({f'B_L_{n}':r.pose.bones[f'B_L_{n}'].matrix_basis.copy() for n in ('UpperArm','Forearm','Hand')})
previous={}
for frame,pose in enumerate(keys):
 for n,m in pose.items():
  b=r.pose.bones[n];q=m.to_quaternion()
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame)

r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=out)
