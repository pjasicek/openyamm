import bpy,json
from mathutils import Vector
from pathlib import Path
s=bpy.data.scenes['Goblin Arm Rig Revision'];bpy.context.window.scene=s;r=bpy.data.objects['Goblin Arm Revision Rig'];a=bpy.data.actions[json.loads(s['authored_actions'])['Standing']];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(1)
out=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack/rig_revision/review');cam=s.camera;cam.data.ortho_scale=.38;s.render.resolution_x=700;s.render.resolution_y=700
center=r.pose.bones['mixamorig:RightHand'].matrix@Vector(s['sword_grip_local']);print({'grip_world':list(center),'wrist':list(r.pose.bones['mixamorig:RightHand'].head)})
for name,vec in [('grip_front',(-.4,-1,.2)),('grip_outside',(-1,-.2,.2)),('grip_inside',(1,-.3,.2))]:
 cam.location=center+Vector(vec);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
