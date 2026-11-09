import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round6/jog_source.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['JogSource'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
rows=[]
for f in range(78):
 bpy.context.scene.frame_set(f);rows.append([f,*[r.pose.bones['B_'+s+'_'+n].head.y for s in 'LR' for n in ['Foot','Hand']]])
print('SOURCEY',rows)
