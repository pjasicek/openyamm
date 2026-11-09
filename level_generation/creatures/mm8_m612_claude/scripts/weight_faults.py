import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v1.blend'))
b=bpy.data.objects['Body']
for i in (2074,5808,2438,5611,531,4032,1728,1930):
 v=b.data.vertices[i]
 print('VERT',i,tuple(round(x,4) for x in v.co),[(b.vertex_groups[g.group].name,round(g.weight,4)) for g in v.groups])
