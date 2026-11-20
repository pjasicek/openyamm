import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_sources.blend'));rig=bpy.data.objects['Rig'];G={s:json.loads((P/f'work/grip_pose{suffix}_unrolled.json').read_text())for s,suffix in [('R',''),('L','_left')]}
for role in ['Staff2','Cast1']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in np.linspace(*a.frame_range,7):
  bpy.context.scene.frame_set(int(f),subframe=float(f-int(f)));h={s:rig.pose.bones[f'B_{s}_Hand'].matrix for s in 'LR'};g={s:h[s]@Vector(G[s]['handle_centre_hand_local'])for s in 'LR'};axis=(g['L']-g['R']).normalized();print('SOURCE',role,float(f),{s:round((h[s].to_3x3()@Vector(G[s]['handle_axis_hand_local'])).dot(axis),3)for s in 'LR'},flush=True)
