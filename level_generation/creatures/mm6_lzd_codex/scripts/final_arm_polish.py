"""Relax the free arm; keep finger articulations stable; unwrap roll before splitting it onto twist bones."""
import bpy,math
import numpy as np
from mathutils import Vector,Quaternion,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reduced_before_arm.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
st=bpy.data.actions['Standing'];rig.animation_data.action=st;rig.animation_data.action_slot=st.slots[0];scene.frame_set(0)
handlocal=rig.pose.bones['B_R_Hand'].rotation_quaternion.copy()
for name,child,direction in [('B_R_UpperArm','B_R_Forearm',(-.62,-.18,-1)),('B_R_Forearm','B_R_Hand',(-.32,-.50,-1))]:
 pb=rig.pose.bones[name];m=pb.matrix.copy();q=(rig.pose.bones[child].head-pb.head).rotation_difference(Vector(direction));t=m.translation.copy();m=q.to_matrix().to_4x4()@m;m.translation=t;pb.matrix=m;bpy.context.view_layer.update()
# The wrist continues the relaxed forearm rather than keeping the source's chest-pointing hand.
rig.pose.bones['B_R_Hand'].rotation_quaternion=Quaternion();bpy.context.view_layer.update()
relaxed={n:rig.pose.bones[n].rotation_quaternion.copy()for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand']}
fingers=[b.name for b in rig.pose.bones if b.name.startswith('B_R_Finger')]
relaxed_fingers={n:rig.pose.bones[n].rotation_quaternion.copy()for n in fingers}
a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(21);draw_fingers={n:rig.pose.bones[n].rotation_quaternion.copy()for n in fingers}
def ease(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];end=int(act.frame_range[1]);poses=[]
 for f in range(end+1):
  scene.frame_set(f);row={b.name:b.rotation_quaternion.copy()for b in rig.pose.bones}
  amount=1.
  if act.name=='Attack':amount=1-ease(f/12) if f<12 else ease((f-27)/6)
  elif act.name=='Death':amount=1-ease(f/8)
  elif act.name=='Dead':amount=0
  for n,q in relaxed.items():row[n]=row[n].slerp(q,amount)
  if act.name in ('Walking','Running'):
   for n in relaxed:rig.pose.bones[n].rotation_quaternion=row[n]
   bpy.context.view_layer.update();pb=rig.pose.bones['B_R_Forearm'];m=pb.matrix.copy();t=m.translation.copy();degrees=(-30 if act.name=='Walking'else -50)+3*math.sin(math.tau*f/end);m=Matrix.Rotation(math.radians(degrees),4,'X')@m;m.translation=t;pb.matrix=m;bpy.context.view_layer.update();row[pb.name]=pb.rotation_quaternion.copy()
  grip=ease((f-10)/8)*(1-ease((f-23)/8)) if act.name=='Attack'else 0
  for n in fingers:row[n]=relaxed_fingers[n].slerp(draw_fingers[n],grip)
  poses.append(row)
 for f,row in enumerate(poses):
  for n in list(relaxed)+fingers:
   pb=rig.pose.bones[n];pb.rotation_quaternion=row[n];pb.keyframe_insert('rotation_quaternion',frame=f)
 # Continuity matters before multiplying the roll by one half; wrapped +/-pi otherwise becomes a 180-degree snap.
 for side in 'LR':
  fa=rig.data.bones[f'B_{side}_Forearm'];ha=rig.data.bones[f'B_{side}_Hand'];ua=rig.data.bones[f'B_{side}_UpperArm'];axes=[(fa.matrix_local.inverted()@ha.head_local).normalized(),(ua.matrix_local.inverted()@fa.head_local).normalized()];angles=[]
  for f in range(end+1):
   scene.frame_set(f);rel=(rig.pose.bones[fa.name].matrix.inverted()@rig.pose.bones[ha.name].matrix).to_quaternion();rest=(fa.matrix_local.inverted()@ha.matrix_local).to_quaternion();qs=[rel@rest.inverted(),rig.pose.bones[ua.name].matrix_basis.to_quaternion()];angles.append([2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)for q,axis in zip(qs,axes)])
  angles=np.unwrap(np.array(angles),axis=0)
  for f,values in enumerate(angles):
   for kind,axis,value,factor in zip(['ForearmTwist','UpperArmTwist'],axes,values,[.5,-.5]):
    pb=rig.pose.bones[f'B_{side}_{kind}'];pb.rotation_quaternion=Quaternion(axis,float(value*factor));pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_reduced.blend'))
