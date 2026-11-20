"""Closed analysis volumes for genuinely open costume pieces; runtime topology is unchanged."""
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def closed_faces(me,pv,faces):
 parts={}
 for pid in set(pv):
  bm=bmesh.new();src=bm.verts.layers.int.new('source');physical=bm.faces.layers.int.new('physical');ids=sorted({i for fc in faces if pv[fc[0]]==pid for i in fc});mapping={i:bm.verts.new(me.vertices[i].co)for i in ids}
  for i,v in mapping.items():v[src]=i
  for fc in faces:
   if pv[fc[0]]==pid:
    try:f=bm.faces.new([mapping[i]for i in fc]);f[physical]=1
    except ValueError:pass
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
  result=bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
  for f in result['faces']:f[physical]=0
  parts[int(pid)]=([tuple(v[src]for v in f.verts)for f in bm.faces],[bool(f[physical])for f in bm.faces]);bm.free()
 return parts
DIRECTIONS=[Vector(v).normalized()for v in [(1,.173,.291),(.237,1,.319),(.127,.239,1)]]
def inside(point,tree):
 votes=0
 for direction in DIRECTIONS:
  origin=point.copy();hits=0
  for _ in range(128):
   loc,_,_,distance=tree.ray_cast(origin,direction,4)
   if loc is None:break
   hits+=1;origin=loc+direction*.000002
  votes+=hits%2
 return votes>=2
cube=[Vector(v)for v in [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]]
ct=BVHTree.FromPolygons(cube,[(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
assert inside(Vector((.5,.5,.5)),ct)and not inside(Vector((1.2,.5,.5)),ct)
