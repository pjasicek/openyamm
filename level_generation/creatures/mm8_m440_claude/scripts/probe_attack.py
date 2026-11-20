from pathlib import Path
import bpy,json,sys
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_grip.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Attack'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
g=json.loads((p/'work/grip_pose.json').read_text());c=Vector(g['handle_centre_hand_local']);a=Vector(g['handle_axis_hand_local']);rows=[]
for f in range(15,41):
 sc.frame_set(f);H=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix;head=H@(c+a*.70)
 rows.append({'frame':f,'time':f/30,'club_head':list(head)})
(p/'work/attack_head_trace.json').write_text(json.dumps(rows,indent=2));print('HEAD_TRACE',rows)
