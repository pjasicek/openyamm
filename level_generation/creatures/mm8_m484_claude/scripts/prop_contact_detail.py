import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_cloth.blend'));o=bpy.data.objects['AxeMesh'];r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Attack'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(23)
for i in [572,580,583,588]:print('AXE VERT',i,list(o.data.vertices[i].co))
for sd in 'RL':
 G=json.loads((P/f'work/grip_pose_{sd}.json').read_text());print('GRIP',sd,G['radius'])
