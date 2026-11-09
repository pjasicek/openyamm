import bpy,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v5.blend'));r=bpy.data.objects['Rig'];G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'RL'};out={}
for nm,frames in {'Standing':[0],'Attack':[0,12,18,24,32,44],'Death':[0,24,48],'Fidget':[20,40]}.items():
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
 for f in frames:
  bpy.context.scene.frame_set(f);row={'f':f,'range':list(a.frame_range)}
  for s in 'RL':
   m=r.matrix_world@r.pose.bones[f'B_{s}_Hand'].matrix;row[s]={'center':list(m@Vector(G[s]['handle_centre_hand_local'])),'axis':list((m.to_3x3()@Vector(G[s]['handle_axis_hand_local'])).normalized()),'shoulder':list(r.pose.bones[f'B_{s}_UpperArm'].head),'wrist':list(m.translation),'elbow':list(r.pose.bones[f'B_{s}_Forearm'].head)}
  rows.append(row)
 out[nm]=rows
(P/'work/motion_probe.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
