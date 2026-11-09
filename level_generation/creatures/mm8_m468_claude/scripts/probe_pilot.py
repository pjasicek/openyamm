import bpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_raw.blend'));r=bpy.data.objects['Rig']
for role,fs in [('Standing',[0]),('Attack',[0,10,20,25,30,35,40,50,79])]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in fs:
  bpy.context.scene.frame_set(f);print('POSE',role,f,{n:[round(x,3) for x in r.pose.bones[n].head] for n in ['B_Pelvis','B_Head','B_R_Hand','B_L_Hand','B_R_Foot','B_L_Foot']})
