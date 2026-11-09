import bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uv_ready.blend'))
me=bpy.data.objects['Body'].data;seen={}
for f in me.polygons:
 key=tuple(sorted(tuple(round(c,6) for c in me.vertices[v].co) for v in f.vertices))
 if key in seen:
  other=me.polygons[seen[key]]
  print('COINCIDENT',f.index,other.index,'normaldot',f.normal.dot(other.normal),'co',key,'piece',me.attributes['piece'].data[f.vertices[0]].value,flush=True)
 else:seen[key]=f.index
