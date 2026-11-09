"""Short native loin panels hinge at the belt and follow the leading thigh without stretching across both legs."""
from pathlib import Path
import bpy, numpy as np, math
from mathutils import Vector, Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5t.blend'))
rig=bpy.data.objects['Rig']; body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for name,y in [('LoinFront',-.13),('LoinBack',.14)]:
 b=rig.data.edit_bones.get(name) or rig.data.edit_bones.new(name);b.head=(0,y,1.035);b.tail=(0,y,.75);b.parent=rig.data.edit_bones['B_Pelvis']
bpy.ops.object.mode_set(mode='OBJECT')
for name,piece in [('LoinFront',19)]:
 group=body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
 ids=[v.index for v in me.vertices if me.attributes['piece'].data[v.index].value==piece]
 assert ids
 for g in body.vertex_groups:
  if g!=group:g.remove(ids)
 group.add(ids,1,'REPLACE')
with bpy.data.libraries.load(str(p/'work/rig_v5.blend'),link=False) as (src,dst):
 dst.objects=['Body']
old=dst.objects[0]
for v in old.data.vertices:
 if old.data.attributes['piece'].data[v.index].value==0:
  # The upper rear panel crossed this small skin patch in Walking frame 4.
  c=Vector((math.copysign(.15181,v.co.x),.04686,1.02490));d=(v.co-c).length
  if d<.065:
   direction=Vector((v.co.x,v.co.y,0)).normalized()
   me.vertices[v.index].co=v.co-direction*(.012*(1-(d/.065)**2)**2)
 if old.data.attributes['piece'].data[v.index].value!=14:continue
 me.vertices[v.index].co=v.co+Vector((0,0.025,0))
 for group in body.vertex_groups:group.remove([v.index])
 for e in v.groups:
  body.vertex_groups[old.vertex_groups[e.group].name].add([v.index],e.weight,'REPLACE')
bpy.data.objects.remove(old,do_unlink=True)
pelrest=rig.data.bones['B_Pelvis'].matrix_local
axes={n:(rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0))).normalized()
      for n in ['LoinFront','LoinBack']}
restangles={}
for side in 'LR':
 d=rig.data.bones[f'B_{side}_Calf'].head_local-rig.data.bones[f'B_{side}_Thigh'].head_local
 restangles[side]=math.atan2(-d.y,-d.z)
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 maxfront=maxback=0
 for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
  bpy.context.scene.frame_set(f)
  undo=(rig.pose.bones['B_Pelvis'].matrix@pelrest.inverted()).inverted().to_3x3()
  angles=[]
  for side in 'LR':
   d=undo@(rig.pose.bones[f'B_{side}_Calf'].head-rig.pose.bones[f'B_{side}_Thigh'].head)
   angles.append(math.atan2(-d.y,-d.z)-restangles[side])
  front=-max(0,*angles)*1.12-math.radians(8)
  back=-min(0,*angles)*1.12+math.radians(8)
  for name,angle in [('LoinFront',front),('LoinBack',back)]:
   pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(axes[name],angle)
   pb.keyframe_insert('rotation_quaternion',frame=f)
  maxfront=max(maxfront,abs(front));maxback=max(maxback,back)
 print('LOIN',act.name,math.degrees(maxfront),math.degrees(maxback))
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v5t.blend'))
