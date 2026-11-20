from pathlib import Path
import bpy,json
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/authored.blend'))
r=bpy.data.objects['Rig'];c=bpy.data.objects['Club'];G=json.loads((p/'work/grip_pose.json').read_text())
print('CLUBWORLD',list(c.matrix_world));print('RIGWORLD',list(r.matrix_world));print('PARENTINV',list(c.matrix_parent_inverse))
a=bpy.data.actions['Fidget'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for f in (5,10,15,20,25,30,35):
 bpy.context.scene.frame_set(f);h=r.pose.bones['B_R_Hand'];head=r.pose.bones['B_Head']
 mouth=head.matrix@head.bone.matrix_local.inverted()@Vector((-.035,-.255,1.355))
 target=h.matrix@Vector(G['handle_centre_hand_local'])+(h.matrix.to_3x3()@Vector(G['handle_axis_hand_local']))*.28
 print('FEED',f,'mouth',tuple(mouth),'clubmeat',tuple(target),'gap',(target-mouth).length,'wrist',tuple(h.head))
