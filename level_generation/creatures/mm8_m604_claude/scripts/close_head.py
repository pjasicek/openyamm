"""Close the remaining small head scan holes; extend adjacent UV charts without moving the surface."""
import bpy,bmesh,json
from pathlib import Path
from mathutils import geometry
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured.blend'));body=bpy.data.objects['Body'];me=body.data
bm=bmesh.new();bm.from_mesh(me);piece=bm.verts.layers.int['piece'];head=bm.faces.layers.int['head']
uvs=list(bm.loops.layers.uv.values());edges={e for e in bm.edges if e.is_boundary and all(v[piece]==60 for v in e.verts)}
added=[]
while edges:
 edge=edges.pop();start,at=edge.verts;cycle=[start,at]
 while at != start:
  links=[e for e in at.link_edges if e in edges]
  assert len(links)==1,('non-cyclic head hole',len(links))
  edge=links[0];edges.remove(edge);at=edge.other_vert(at)
  if at!=start:cycle.append(at)
 assert len(cycle)<=8
 neighbours={f for v in cycle for f in v.link_faces}
 for i in range(1,len(cycle)-1):
  vs=[cycle[0],cycle[i],cycle[i+1]]
  nf=bm.faces.new(vs);nf[head]=1;nf.smooth=True
  near=max(neighbours,key=lambda f:(len(set(f.verts)&set(vs)),-(f.calc_center_median()-nf.calc_center_median()).length))
  a,b,c=list(near.verts)[:3]
  for uv in uvs:
   uvbyv={l.vert:l[uv].uv.copy() for l in near.loops}
   from mathutils import Vector
   ta,tb,tc=[Vector((*uvbyv[v],0)) for v in (a,b,c)]
   for l in nf.loops:l[uv].uv=geometry.barycentric_transform(l.vert.co,a.co,b.co,c.co,ta,tb,tc).xy
  added.append(nf)
bmesh.ops.recalc_face_normals(bm,faces=added)
assert not [e for e in bm.edges if e.is_boundary and all(v[piece]==60 for v in e.verts)]
report={'new_head_cap_triangles':len(added),'preserved_vertices':len(bm.verts)}
bm.to_mesh(me);bm.free();me.update();print('HEAD CAPS',report)
(p/'work/head_caps.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/ready.blend'))
