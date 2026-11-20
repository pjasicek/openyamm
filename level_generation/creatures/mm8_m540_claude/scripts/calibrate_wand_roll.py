from pathlib import Path
import bpy,math,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilots_fitted.blend'));rig=bpy.data.objects['Rig']
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
M=rig.pose.bones['Wand'].matrix;axis=M.to_3x3().col[2].normalized();front=-M.to_3x3().col[1]
target=Vector((0,-1,0));target=(target-axis*target.dot(axis)).normalized();front=(front-axis*front.dot(axis)).normalized()
delta=math.atan2(axis.dot(front.cross(target)),front.dot(target))
row={'roll_radians':math.pi+delta,'correction_degrees':math.degrees(delta),'purpose':'Skull face points toward the target in the native ready stance'}
(p/'work/wand_orientation.json').write_text(json.dumps(row,indent=2)+'\n');print('WAND_ROLL',row)
