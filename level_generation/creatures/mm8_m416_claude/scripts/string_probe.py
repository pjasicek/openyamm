from pathlib import Path
import bpy,json
from mathutils import Vector
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm8_m416_claude');bpy.ops.wm.open_mainfile(filepath=str(P/'work/equipped.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(21);cfg=json.loads((P/'work/props.json').read_text())
for i,s in enumerate('LR'):
 p=r.pose.bones['String'+s];C=r.pose.bones['Crossbow'].matrix
 print('STRING',s,'basis',list(p.location),list(p.scale),'start',list(p.matrix.translation),'expected',list(C@Vector(cfg['string_tips'][i])))
 o=bpy.data.objects['String'+s+'Mesh'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();print('MESH',list(me.vertices[0].co),list(me.vertices[-1].co));ev.to_mesh_clear()
