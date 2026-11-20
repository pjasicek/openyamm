import bpy,json
from pathlib import Path
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');grip=json.loads((OUT/'grip_pose.json').read_text());count=0
for name in ['Idle','Walk','Run','GripRest','Attack']:
 a=bpy.data.actions['MM6_Goblin_'+name]
 for layer in a.layers:
  for st in layer.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for bn,data in grip.items():
      for prop,key in [('rotation_quaternion','rotation'),('location','location')]:
       if fc.data_path=='pose.bones["'+bn+'"].'+prop:
        val=data[key][fc.array_index]
        for kp in fc.keyframe_points:kp.co.y=val
        count+=1
s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;r=s.objects['Goblin_Combat_Rig'];a=bpy.data.actions['MM6_Goblin_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(1);print('Updated',count,'finger channels using coherent bind-space thumb transforms')
