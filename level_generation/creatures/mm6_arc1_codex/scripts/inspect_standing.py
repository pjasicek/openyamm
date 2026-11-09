import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand','B_R_Finger2']:
 b=r.pose.bones[n];print('STAND',n,'head',list(b.head),'tail',list(b.tail),'q',list(b.rotation_quaternion))
