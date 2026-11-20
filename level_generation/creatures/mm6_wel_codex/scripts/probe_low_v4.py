import bpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_master.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
for n in ['Root','B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_R_Clavicle','B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_UpperArm','B_L_Forearm','B_L_Hand','Trident']:
 b=r.pose.bones[n];print(n,'world',list(b.matrix.translation),'localq',list(b.rotation_quaternion),'parent',b.parent.name if b.parent else None)
