import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/gate_master.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;hf=json.loads((P/'work/hand_frames.json').read_text())['L']
for name,t in [('Standing',0),('Cast',.375),('Attack',.5),('Death',2.0)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*sc.render.fps;sc.frame_set(int(f),subframe=f%1);print('POSE',name,t,flush=True)
 for n in ['B_L_Clavicle','B_L_UpperArm','B_L_Forearm','B_L_Hand','LeafShield']:
  b=rig.pose.bones[n];print(n,'head',list(b.head),'loc',list(b.location),'scale',list(b.scale),'qlen',b.rotation_quaternion.magnitude,flush=True)
 H=rig.pose.bones['B_L_Hand'].matrix;print('long/palm',list(H.to_3x3()@Vector(hf['long_local'])),list(H.to_3x3()@Vector(hf['palm_local'])),flush=True)
