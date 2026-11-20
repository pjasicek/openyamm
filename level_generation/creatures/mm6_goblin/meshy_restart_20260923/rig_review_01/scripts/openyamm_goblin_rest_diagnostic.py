import bpy,json
from pathlib import Path
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01');s=bpy.data.scenes['Goblin - Meshy Rig Diagnosis'];bpy.context.window.scene=s;arm=next(o for o in s.objects if o.type=='ARMATURE');a=bpy.data.actions['restpose'];arm.data.pose_position='POSE';arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];s.frame_set(1);rows=[]
for b in arm.pose.bones:
 delta=b.matrix@b.bone.matrix_local.inverted();rows.append({'bone':b.name,'pose_head':list(arm.matrix_world@b.head),'bind_head':list(arm.matrix_world@b.bone.head_local),'delta_angle_degrees':delta.to_quaternion().angle*180/3.141592653589793,'delta_translation':list(delta.translation)})
(OUT/'restpose_deformation.json').write_text(json.dumps(rows,indent=2))
s.view_layers[0].material_override=None;s.render.filepath=str(OUT/'restpose_action.png');bpy.app.timers.register(lambda: (bpy.ops.render.render(write_still=True) and None),first_interval=.1);print(json.dumps(rows[:8]))
