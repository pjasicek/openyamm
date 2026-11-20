import bpy,bmesh,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
report={}
for r in json.loads((P/'ownership.json').read_text()):
 bpy.ops.wm.open_mainfile(filepath=str(P/'references/scenes'/f"{r['source_design']}.blend"))
 obj=bpy.data.objects[r['source_design']];bm=bmesh.new();bm.from_mesh(obj.data);bm.normal_update()
 before=[f.normal.copy() for f in bm.faces]
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 coords=[obj.matrix_world@v.co for v in bm.verts]
 entry={'verts':len(bm.verts),'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold for e in bm.edges),'flipped_faces':sum(a.dot(f.normal)<0 for a,f in zip(before,bm.faces)),'bounds':[[min(v[i] for v in coords) for i in range(3)],[max(v[i] for v in coords) for i in range(3)]],'materials':[m.name for m in obj.data.materials]}
 seen=set();groups=[]
 for v in bm.verts:
  if v in seen:continue
  stack=[v];seen.add(v);vs=[]
  while stack:
   a=stack.pop();vs.append(a)
   for e in a.link_edges:
    b=e.other_vert(a)
    if b not in seen:seen.add(b);stack.append(b)
  groups.append({'verts':len(vs),'bounds':[[min(v.co[i] for v in vs) for i in range(3)],[max(v.co[i] for v in vs) for i in range(3)]]})
 entry['components']=groups
 if r['family']=='boots':
  entry['upper_boots']=[]
  for sign in [-1,1]:
   vs=[v for v in bm.verts if v.co.x*sign>0 and v.co.z>.7]
   entry['upper_boots'].append({'mean':[sum(v.co[i] for v in vs)/len(vs) for i in range(3)],'bounds':[[min(v.co[i] for v in vs) for i in range(3)],[max(v.co[i] for v in vs) for i in range(3)]]})
 report[r['icon']]=entry;bm.free()
(P/'receipts/scene_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
