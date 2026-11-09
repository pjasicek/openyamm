"""Use a low sword-ready idle, settle the forward fall, and freeze its final corpse."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Quaternion,Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;scene.render.fps=30
G=json.loads((p/'work/grip_pose.json').read_text());axis=Vector(G['handle_axis_hand_local'])
def setact(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snapshot():
 return {pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones}
def write(name,frames):
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;setact(a);prev={}
 for f,pose in enumerate(frames):
  for n,(q,l) in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
   pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(frames)-1;setact(None)
for name in ('Standing','Fidget'):
 a=bpy.data.actions[name];setact(a);frames=[]
 for f in range(int(a.frame_range[1])+1):
  scene.frame_set(f);pose=snapshot();hand=rig.pose.bones['B_R_Hand']
  H=hand.matrix.copy();v=(H.to_3x3()@axis).normalized()
  target=Vector((v.x,v.y,-math.tan(math.radians(30))*math.hypot(v.x,v.y))).normalized()
  desired=(v.rotation_difference(target).to_matrix()@H.to_3x3()).to_4x4();desired.translation=H.translation
  parent=hand.parent;restlocal=parent.bone.matrix_local.inverted()@hand.bone.matrix_local
  local=restlocal.inverted()@parent.matrix.inverted()@desired
  pose[hand.name]=(local.to_quaternion(),pose[hand.name][1]);frames.append(pose)
 write(name,frames)
setact(bpy.data.actions['Standing']);scene.frame_set(0);ready=snapshot();ready_world={n:rig.pose.bones[n].matrix.to_quaternion() for n in [f'B_R_{v}' for v in ['UpperArm','Forearm','Hand']]}
for name in ('Walking','Running'):
 a=bpy.data.actions[name];setact(a);frames=[]
 for f in range(int(a.frame_range[1])+1):
  scene.frame_set(f)
  if name=='Walking':
   # Native gait keeps the sword in a low ready carry.
   for part in ['UpperArm','Forearm','Hand']:
    n=f'B_R_{part}';pb=rig.pose.bones[n];M=(Matrix.Rotation(math.radians(-15),3,'X')@ready_world[n].to_matrix()).to_4x4()
    M.translation=pb.head;pb.matrix=M;bpy.context.view_layer.update()
   pb=rig.pose.bones['B_L_UpperArm'];M=pb.matrix.copy();pivot=M.translation.copy()
   M=Matrix.Rotation(math.radians(-10),4,'X')@M;M.translation=pivot;pb.matrix=M
   bpy.context.view_layer.update()
  for side in 'LR':
   for part,amount in [('Thigh',.8 if name=='Walking' else .7),('Calf',.7 if name=='Walking' else .65)]:
    pb=rig.pose.bones[f'B_{side}_{part}'];pb.rotation_quaternion=Quaternion().slerp(pb.rotation_quaternion,amount)
  bpy.context.view_layer.update()
  ob=bpy.data.objects['Body'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  bottom=min((ob.matrix_world@v.co).z for v in me.vertices)
  ev.to_mesh_clear()
  pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation.z-=bottom;pb.matrix=M
  bpy.context.view_layer.update();frames.append(snapshot())
 write(name,frames)
a=bpy.data.actions['Hit'];setact(a);frames=[]
last=int(a.frame_range[1])
for f in range(last+1):
 scene.frame_set(f);pose=snapshot()
 for n in pose:
  if n.startswith('B_L_Finger'):pose[n]=(ready[n][0],pose[n][1])
 t=max(0,(f-(last-5))/5);t=t*t*(3-2*t)
 if t:
  for n,(q,l) in pose.items():pose[n]=(q.slerp(ready[n][0],t),l.lerp(ready[n][1],t))
 frames.append(pose)
write('Hit',frames)
a=bpy.data.actions['Death'];setact(a);frames=[]
for f in range(int(a.frame_range[1])+1):scene.frame_set(f);frames.append(snapshot())
frames.extend([frames[-1]]*15)
write('Death',frames);write('Dead',[frames[-1],frames[-1]])
# Ground the body before simulating any cloth.
import numpy as np
body=bpy.data.objects['Body'];pv=np.zeros(len(body.data.vertices),np.int32);body.data.attributes['piece'].data.foreach_get('value',pv)
for name in ['Standing','Fidget','Walking','Running','Attack','Hit','Death','Dead']:
 a=bpy.data.actions[name];setact(a);frames=[]
 solid=np.where(~np.isin(pv,[0,8,9]) if name in ['Death','Dead'] else np.isin(pv,[2,6,7]))[0]
 for f in range(int(a.frame_range[1])+1):
  scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
  bottom=min((body.matrix_world@mesh.vertices[int(i)].co).z for i in solid);ev.to_mesh_clear()
  pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation.z-=bottom;pb.matrix=M
  bpy.context.view_layer.update();frames.append(snapshot())
 write(name,frames)
assert bpy.data.actions['Hit'].frame_range[1]/30<=.75
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v6.blend'))
