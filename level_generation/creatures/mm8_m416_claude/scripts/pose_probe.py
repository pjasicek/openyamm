from pathlib import Path
import bpy,sys,json
from mathutils import Vector
P=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm8_m416_claude')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fingered.blend'));r=bpy.data.objects['Rig']
for an in ['Standing','AimSource']:
 a=bpy.data.actions[an];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
 print('POSE',an)
 for s in ['R','L']:
  g=json.loads((P/('work/grip_pose.json' if s=='R' else 'work/grip_pose_L.json')).read_text());H=r.matrix_world@r.pose.bones[f'B_{s}_Hand'].matrix
  print(s, 'shoulder',list(r.pose.bones[f'B_{s}_UpperArm'].head),'elbow',list(r.pose.bones[f'B_{s}_Forearm'].head),'hand',list(H.translation),'grip',list(H@Vector(g['handle_centre_hand_local'])),'axis',list(H.to_3x3()@Vector(g['handle_axis_hand_local'])), 'rotation',list(H.to_quaternion()))
