import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_uv.blend'))
o=bpy.data.objects['Body'];m=o.data;seen={}
for p in m.polygons:
 key=tuple(sorted(tuple(round(x,6) for x in m.vertices[i].co) for i in p.vertices))
 if key in seen:
  q=m.polygons[seen[key]]
  print('DUPLICATE',q.index,p.index,'piece',[m.attributes['piece'].data[i].value for i in p.vertices],'vertices',q.vertices[:],p.vertices[:],'normals',q.normal[:],p.normal[:],'weights',[[[(o.vertex_groups[g.group].name,round(g.weight,6)) for g in m.vertices[i].groups if g.weight>1e-6] for i in f.vertices] for f in (q,p)],flush=True)
 else:seen[key]=p.index

for i in (5720,5721,5722,5723):
 p=m.polygons[i];print('FACE',i,'area',p.area,'verts',[m.vertices[v].co[:] for v in p.vertices],'piece',[m.attributes['piece'].data[v].value for v in p.vertices],flush=True)
small=sorted((p.area,p.index) for p in m.polygons)[:8];print('SMALLEST',small,flush=True)
