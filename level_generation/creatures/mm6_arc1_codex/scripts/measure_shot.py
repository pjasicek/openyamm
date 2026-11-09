import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'));r=bpy.data.objects['Rig'];g=json.loads((P/'work/grip_pose.json').read_text());a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for f in [24,30,31,34,35,36,37,38]:
 bpy.context.scene.frame_set(f);h=r.pose.bones['B_L_Hand'].matrix;c=h@Vector(g['handle_centre_hand_local']);up=h.to_3x3()@Vector(g['handle_axis_hand_local']);n=r.pose.bones['B_R_Finger1'].head;d=c-n
 print('SHOT',f,'bow',list(c),'nock',list(n),'up',list(up),'aimyaw',math.degrees(math.atan2(d.x,-d.y)),'pitch',math.degrees(math.atan2(d.z,math.hypot(d.x,d.y))))

for name in ['Standing','Walking','Running','Hit','Fidget','Cast','Death','Dead']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(int(a.frame_range[1]/2));h=r.pose.bones['B_L_Hand'].matrix;print('BOWUP',name,list(h.to_3x3()@Vector(g['handle_axis_hand_local'])))
