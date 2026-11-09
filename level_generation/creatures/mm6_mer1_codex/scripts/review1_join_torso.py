import bpy,bmesh,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sel=json.loads((P/'review/reduction/selection.json').read_text());axes=[Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
for e in [{'blend':'work/reduction_master.blend'}]+sel['body']:
 path=P/e['blend'];bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['Body'];parts=[a.value for a in o.data.attributes['piece'].data];o.data.calc_loop_triangles();co=[v.co.copy()for v in o.data.vertices];tris=[t for t in o.data.loop_triangles if all(parts[i]==1 for i in t.vertices)];tree=BVHTree.FromPolygons(co,[t.vertices[:]for t in tris],all_triangles=True)
 for v in o.data.vertices:
  if parts[v.index]not in[8,9]or abs(v.co.x)>=.185 or v.co.z<1.15:continue
  hit,n,fi,dist=tree.find_nearest(v.co);assert hit is not None;t=tris[fi];w=barycentric_transform(hit,*[co[i]for i in t.vertices],*axes);weights={}
  for vi,a in zip(t.vertices,w):
   for g in o.data.vertices[vi].groups:weights[g.group]=weights.get(g.group,0)+max(0,a)*g.weight
  v.co=hit-n*.015
  for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
  total=sum(weights.values())
  for gi,value in weights.items():
   if value>1e-8:o.vertex_groups[gi].add([v.index],value/total,'REPLACE')
 bm=bmesh.new();bm.from_mesh(o.data);part=bm.verts.layers.int['piece'];faces=[f for f in bm.faces if all(v[part]in[8,9]for v in f.verts)];bmesh.ops.recalc_face_normals(bm,faces=faces);bm.to_mesh(o.data);bm.free();bpy.ops.wm.save_as_mainfile(filepath=str(path))
