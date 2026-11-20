"""Keep the native moderate crouch; rigid head accessories; ground the fitted skeleton."""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
# Separate eyes, teeth and hair all belong to the head.
piece=np.array([x.value for x in body.data.attributes['piece'].data])
for v in body.data.vertices:
 if piece[v.index]>=4:
  for g in body.vertex_groups: g.remove([v.index])
  body.vertex_groups['B_Head'].add([v.index],1.,'REPLACE')
def action(a):
 rig.animation_data.action=a
 if a and len(a.slots): rig.animation_data.action_slot=a.slots[0]
for name in ['Standing','Fidget','Attack','Hit']:
 a=bpy.data.actions[name]; poses=[]
 for fr in range(int(a.frame_range[1])+1):
  action(a);sc.frame_set(fr)
  snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
  action(None)
  for b in rig.pose.bones: b.matrix_basis=snap[b.name]
  for sd in 'LR':
   for part in ['Thigh','Calf']:
    b=rig.pose.bones[f'B_{sd}_{part}'];b.rotation_mode='QUATERNION'
    b.rotation_quaternion=Quaternion().slerp(b.rotation_quaternion,0.66)
  bpy.context.view_layer.update()
  poses.append({b.name:b.rotation_quaternion.copy() for b in rig.pose.bones if b.name.endswith(('Thigh','Calf'))})
 action(a)
 for fr,pose in enumerate(poses):
  for n,q in pose.items():
   b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=fr)
print('POSTURE native moderate crouch: thigh/calf rotation 66 percent in guard-based clips')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_posture.blend'))
