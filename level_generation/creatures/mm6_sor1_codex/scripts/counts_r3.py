import bpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for level in ['motion','lod0','lod1','lod2','lod3']:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work'/f'round3_{level}.blend'));me=bpy.data.objects['Body'].data;v=me.attributes['piece'].data;counts={}
 for f in me.polygons:
  part=v[f.vertices[0]].value;counts[part]=counts.get(part,0)+len(f.vertices)-2
 print('PART_COUNTS',level,counts,flush=True)
