from pathlib import Path
import bpy,math
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_raw.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for f in range(12):
 bpy.context.scene.frame_set(f);row=[]
 for n in ['B_Pelvis','B_Spine2','B_Head']:
  d=r.pose.bones[n].matrix.to_3x3()@r.data.bones[n].matrix_local.to_3x3().inverted()@Vector((0,-1,0));row.append(round(math.degrees(math.atan2(d.y,d.x)),1))
 print('RAW_DEATH',f,row)
