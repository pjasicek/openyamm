import bpy,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/texture_master.blend'));b=bpy.data.objects['Body'];me=b.data
for i in [6558,6688,6689,6738]:
 f=me.polygons[i];print('OMITTED',i,'part',[me.attributes['piece'].data[v].value for v in f.vertices],'area',f.area,'co',[list(me.vertices[v].co) for v in f.vertices],flush=True)
uv=me.uv_layers['HeadUV'].data;P=[];areas=[]
for f in me.polygons:
 if me.attributes['head'].data[f.index].value:
  a,bb,c=[np.array(uv[i].uv) for i in f.loop_indices];areas.append(abs(np.cross(bb-a,c-a))/2);P.extend([a,bb,c])
P=np.array(P);print('HEADUV',len(areas),'sumarea',sum(areas),'zero',sum(x<1e-9 for x in areas),'bbox',P.min(0),P.max(0))
