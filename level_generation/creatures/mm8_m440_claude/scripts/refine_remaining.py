from pathlib import Path
import bpy,sys,math,json,numpy as np
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_runfit.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
parts=np.array([a.value for a in body.data.attributes['piece'].data]);feet=np.flatnonzero(np.isin(parts,[4,5]))
def act(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snap(a,f):
 act(a);sc.frame_set(int(f),subframe=f-int(f));return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def restore(x):
 act(None)
 for n,m in x.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def mix(a,b,w):
 x={}
 for n in a:
  q=a[n].to_quaternion();r=b[n].to_quaternion()
  if q.dot(r)<0:r=-r
  m=q.slerp(r,w).to_matrix().to_4x4();m.translation=a[n].translation.lerp(b[n].translation,w);x[n]=m
 return x
def write(name,frames):
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;act(a);prev={}
 for i,x in enumerate(frames):
  for n,m in x.items():
   b=rig.pose.bones[n];q=m.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=i/2)
   if n=='B_Pelvis':b.location=m.translation;b.keyframe_insert('location',frame=i/2)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=(len(frames)-1)/2
st=snap(bpy.data.actions['Standing'],0)
# The death starts from the selected guard; preserve every source fall frame after an eight-frame transition.
with bpy.data.libraries.load(str(p/'work/full_grip.blend'),link=False) as (a,b):b.actions=['Death']
rawdeath=b.actions[0]
import action_curves
for a in bpy.data.actions:action_curves.continuous(a)
d0=snap(rawdeath,0)
for name in ('Fidget','Death','Running','Hit'):
 a=rawdeath if name=='Death' else bpy.data.actions[name];N=40 if name=='Death' else int(a.frame_range[1]);frames=[]
 for i in range(N*2+1):
  f=i/2
  if name=='Death':
   if f<12:
    w=f/12;w=w*w*(3-2*w);x=mix(st,snap(a,4*(f/12)**3),w)
   else:x=snap(a,f-8)
  else:x=snap(a,f)
  if name=='Fidget':
   for n in x:
    if n=='B_Pelvis' or any(k in n for k in ('Thigh','Calf','Foot','Toe')):x[n]=st[n]
  restore(x)
  if name in ('Fidget','Death'):
   for n in ('B_Neck','B_Head'):
    q0=st[n].to_quaternion();q=rig.pose.bones[n].matrix_basis.to_quaternion()
    if q0.dot(q)<0:q=-q
    rig.pose.bones[n].rotation_quaternion=q0.slerp(q,.38 if name=='Fidget' else .45)
   bpy.context.view_layer.update()
  if name=='Fidget':
   H=armik.W(rig,'B_L_UpperArm');armik.set_world(rig,'B_L_UpperArm',armik.rot_world(H,Matrix.Rotation(-math.radians(12)*math.sin(math.pi*f/N)**2,3,'Y')@H.to_3x3()))
  if name=='Death':
   for side in 'LR':
    # Cap the relaxed wrist's bend against the actual palm axis, retaining the fall's roll.
    ft,hn=f'B_{side}_ForearmTwist',f'B_{side}_Hand';Fr=rig.data.bones[ft].matrix_local.to_3x3();Hr=rig.data.bones[hn].matrix_local.to_3x3();neutral=armik.W(rig,ft).to_3x3()@Fr.inverted()@Hr
    H=armik.W(rig,hn);R=neutral.inverted()@H.to_3x3();fingers=[rig.data.bones[f'B_{side}_Finger{k}'].head_local for k in range(5)];axis=(Hr.inverted()@(sum(fingers,Vector())/5-rig.data.bones[hn].head_local)).normalized();posed=(R@axis).normalized();angle=axis.angle(posed)
    if angle>math.radians(65):
     correction=Quaternion(posed.cross(axis).normalized(),angle-math.radians(65));armik.set_world(rig,hn,armik.rot_world(H,neutral@correction.to_matrix()@R))
  for side in 'LR':rig.pose.bones[f'B_{side}_Toe0'].matrix_basis=Matrix()
  bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=np.array([(body.matrix_world@v.co).z for v in me.vertices]);ev.to_mesh_clear();low=float(z.min() if name=='Death' else z[feet].min())
  M=armik.W(rig,'B_Pelvis');M.translation.z+=.003-low;armik.set_world(rig,'B_Pelvis',M)
  frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
 if name=='Running':frames[-1]=frames[0]
 write(name,frames)
 if name=='Death':write('Dead',[frames[-1],frames[-1],frames[-1]])
bpy.data.actions.remove(rawdeath);act(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_repaired.blend'))
