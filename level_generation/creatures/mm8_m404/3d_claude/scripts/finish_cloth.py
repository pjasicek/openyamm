"""Keep the leather apron in front of the leading thigh as the hips move."""
import bpy, math
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_motion.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
assert 'B_Loincloth' not in rig.data.bones
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.new('B_Loincloth');b.head=(0,.015,1.12);b.tail=(0,.015,.78);b.align_roll(Vector((0,-1,0)));b.parent=rig.data.edit_bones['B_Pelvis']
bpy.ops.object.mode_set(mode='OBJECT')
ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value==5]
for g in body.vertex_groups:g.remove(ids)
g=body.vertex_groups.new(name='B_Loincloth');g.add(ids,1,'REPLACE')
rest=rig.data.bones['B_Pelvis'].matrix_local.copy();cloth=rig.data.bones['B_Loincloth'].matrix_local.copy()
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];poses=[]
 for i in range(round(float(act.frame_range[1])*4)+1):
  f=i/4;sc.frame_set(int(f),subframe=f%1);D=rig.pose.bones['B_Pelvis'].matrix@rest.inverted();inv=D.inverted()
  angles=[]
  for side in 'LR':
   hip=inv@rig.pose.bones['B_'+side+'_Thigh'].matrix.translation
   knee=inv@rig.pose.bones['B_'+side+'_Calf'].matrix.translation;v=knee-hip
   angles.append(math.atan2(-v.y,-v.z))
  angle=max(0,min(math.radians(80),max(angles)))+math.radians(8)
  rotation=Quaternion((1,0,0),-angle).to_matrix()
  M=D@cloth;M=Matrix.LocRotScale(M.translation,(D.to_3x3()@rotation@cloth.to_3x3()).to_quaternion(),Vector((1,1,1)))
  rig.pose.bones['B_Loincloth'].matrix=M;bpy.context.view_layer.update()
  poses.append(rig.pose.bones['B_Loincloth'].rotation_quaternion.copy())
 prev=None
 for i,q in enumerate(poses):
  if prev is not None and q.dot(prev)<0:q=-q
  pb=rig.pose.bones['B_Loincloth'];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=i/4);prev=q.copy()
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     if 'B_Loincloth' in fc.data_path:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_motion.blend'))
