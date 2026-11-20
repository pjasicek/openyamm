"""Keep coincident garment seam vertices together after skinning without changing their UV corners."""
import bpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
o=bpy.data.objects['Body'];groups={}
for v in o.data.vertices:
 if o.data.attributes['piece'].data[v.index].value==100:
  groups.setdefault(tuple(round(c,6) for c in v.co),[]).append(v)
count=0
for vs in groups.values():
 if len(vs)<2:continue
 w={}
 for v in vs:
  for g in v.groups:w[g.group]=w.get(g.group,0)+g.weight/len(vs)
 keep=sorted(w.items(),key=lambda x:-x[1])[:4];total=sum(x for _,x in keep)
 for v in vs:
  for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
  for n,val in keep:o.vertex_groups[n].add([v.index],val/total,'REPLACE')
 count+=len(vs)
print('COINCIDENT CLOTH weights unified',count)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured_uv.blend'))
