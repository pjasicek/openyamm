import bpy,bmesh,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_weighted.blend'))
m=bpy.data.objects['Body'].data;b=bmesh.new();b.from_mesh(m);pl=b.verts.layers.int['piece'];edges={e for e in b.edges if e.is_boundary};rows=[]
while edges:
 e=edges.pop();todo=[e];vs=set(e.verts);es={e}
 while todo:
  e=todo.pop()
  for v in e.verts:
   for x in v.link_edges:
    if x in edges:edges.remove(x);es.add(x);vs.update(x.verts);todo.append(x)
 xyz=[v.co for v in vs];c=sum(xyz,xyz[0]*0)/len(xyz)
 rows.append(dict(piece=sorted({v[pl] for v in vs}),n=len(es),center=list(c),lo=[min(v[i] for v in xyz) for i in range(3)],hi=[max(v[i] for v in xyz) for i in range(3)]))
print('BOUNDARIES',json.dumps(rows));(p/'review/boundaries.json').write_text(json.dumps(rows,indent=2))
