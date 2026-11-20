import bpy,bmesh,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/club.blend'))
o=bpy.data.objects['ClubMesh'];bm=bmesh.new();bm.from_mesh(o.data);seen=set();report=[]
for v in bm.verts:
 if v in seen:continue
 stack=[v];group=[];seen.add(v)
 while stack:
  x=stack.pop();group.append(x)
  for e in x.link_edges:
   y=e.other_vert(x)
   if y not in seen:seen.add(y);stack.append(y)
 faces=set(f for x in group for f in x.link_faces)
 report.append({'verts':len(group),'faces':len(faces),'bounds':[[min(x.co[k] for x in group) for k in range(3)],[max(x.co[k] for x in group) for k in range(3)]],'seed':list(group[0].co)})
print('CLUBPARTS',json.dumps(report))
long=[{'index':f.index,'vertices':[list(v.co) for v in f.verts]} for f in bm.faces if max((e.calc_length() for e in f.edges),default=0)>.2]
print('LONGFACES',json.dumps(long))
