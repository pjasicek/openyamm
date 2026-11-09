import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_fitted.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for i in [0,5,9,12,15,17,20,24,28,34]:
 sc.frame_set(i);A=r.pose.bones['Axe'].matrix@r.data.bones['Axe'].matrix_local.inverted();print('POSITIONS',i,{'right':list(A@Vector((0,0,.7))),'left':list(A@Vector((0,0,.25))),'axis':list(A.to_3x3()@Vector((0,0,1))),'shoulder':[list(r.pose.bones['B_'+s+'_UpperArm'].head) for s in 'RL']})
