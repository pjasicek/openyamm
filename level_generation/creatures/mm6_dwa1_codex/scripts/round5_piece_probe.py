import bpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['authoring_source','step6']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round5/{name}.blend'));me=bpy.data.objects['Body'].data;p=np.array([x.value for x in me.attributes['piece'].data]);counts={}
 for f in me.polygons:
  key=int(np.bincount(p[list(f.vertices)]).argmax());counts[key]=counts.get(key,0)+len(f.vertices)-2
 print('PIECES',name,counts,flush=True)
