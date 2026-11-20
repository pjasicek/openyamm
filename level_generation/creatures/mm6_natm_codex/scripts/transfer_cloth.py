import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/cloth_stable.blend'));rig=bpy.data.objects['Rig'];poses={};names=[b.name for b in rig.pose.bones if b.name.startswith('Cloth')]
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];poses[act.name]=[]
 for f in range(int(act.frame_range[1])+1):
  bpy.context.scene.frame_set(f);poses[act.name].append({n:(rig.pose.bones[n].location.copy(),rig.pose.bones[n].rotation_quaternion.copy())for n in names})
bpy.ops.wm.open_mainfile(filepath=str(P/'work/contact_master.blend'));rig=bpy.data.objects['Rig']
for name,frames in poses.items():
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for f,pose in enumerate(frames):
  for n,(l,q)in pose.items():pb=rig.pose.bones[n];pb.location=l;pb.rotation_quaternion=q;pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/contact_master.blend'))
