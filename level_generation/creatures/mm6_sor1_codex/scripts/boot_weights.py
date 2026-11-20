import bpy,sys
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(p/src));body=bpy.data.objects['Body'];me=body.data
for v in me.vertices:
 piece=me.attributes['piece'].data[v.index].value
 if piece not in [101,102]:continue
 sd='R' if piece==101 else 'L';calf=float(np.clip((v.co.z-.085)/.07,0,1))
 for g in body.vertex_groups:g.remove([v.index])
 body.vertex_groups[f'B_{sd}_Calf'].add([v.index],calf,'REPLACE');body.vertex_groups[f'B_{sd}_Foot'].add([v.index],1-calf,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/out))
