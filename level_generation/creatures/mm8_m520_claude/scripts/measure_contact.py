from pathlib import Path
import bpy,numpy as np,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm8_m520.blend'));rig=bpy.data.objects['Rig'];path=json.loads((p/'work/boulder_path.json').read_text());rig.animation_data.action=bpy.data.actions['Attack'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
for f in [9,12,15,18,22,24,27,29]:
 bpy.context.scene.frame_set(f);c=Vector(path[f]['centre']);row={'frame':f}
 for s,sign in [('L',1),('R',-1)]:
  hand=rig.data.bones[f'B_{s}_Hand'];kn=sum((rig.data.bones[f'B_{s}_Finger{i}'].head_local for i in range(1,5)),Vector())/4
  palm=hand.matrix_local.inverted()@(hand.head_local+(kn-hand.head_local)*.65)
  world=rig.pose.bones[hand.name].matrix@palm;want=c+Vector((sign*.375,0,-.025));row[s]=[round(v,4) for v in (world-want)]
 print('PALM_TARGET_DELTA',row,flush=True)
