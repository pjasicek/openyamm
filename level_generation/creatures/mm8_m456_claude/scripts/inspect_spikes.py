import bpy,json,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'));o=bpy.data.objects['Body'];me=o.data
for e in me.edges:
 a,b=[me.vertices[i] for i in e.vertices];dist=(a.co-b.co).length
 if dist>.18:print('LONGEDGE',round(dist,3),[(v.index,me.attributes['piece'].data[v.index].value,tuple(round(x,4) for x in v.co)) for v in [a,b]])
print('OBJECT',o.matrix_world)
