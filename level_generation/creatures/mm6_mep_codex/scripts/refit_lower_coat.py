import bpy,numpy as np
from mathutils import Vector,geometry
from mathutils.bvhtree import BVHTree
def refit(b):
 me=b.data;pv=[x.value for x in me.attributes['piece'].data];me.calc_loop_triangles();tri=[tuple(t.vertices) for t in me.loop_triangles if all(pv[i]==1 for i in t.vertices)];tree=BVHTree.FromPolygons([v.co for v in me.vertices],tri,all_triangles=True)
 for v in me.vertices:
  if pv[v.index]!=0 or v.co.z>=1.08 or abs(v.co.x)>=.26:continue
  point,normal,index,distance=tree.find_nearest(v.co);ids=tri[index];coords=[me.vertices[i].co for i in ids];weights=geometry.barycentric_transform(point,*coords,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));src={}
  for i,w in zip(ids,weights):
   for g in me.vertices[i].groups:src[g.group]=src.get(g.group,0)+g.weight*w
  factor=min(1,max(0,(1.08-v.co.z)/.08));old={g.group:g.weight for g in v.groups};new={k:old.get(k,0)*(1-factor)+src.get(k,0)*factor for k in old.keys()|src.keys()};total=sum(new.values())
  for g in list(v.groups):b.vertex_groups[g.group].remove([v.index])
  for k,w in new.items():
   if w>1e-6:b.vertex_groups[k].add([v.index],w/total,'REPLACE')

 # Retain clearance in the hidden trouser layer after its coarse triangles span the coat folds.
 for v in me.vertices:
  if pv[v.index]==1 and v.co.z>.83:
   fade=min(1,max(0,(v.co.z-.83)/.07));center=Vector((.10 if v.co.x>0 else -.10,0,v.co.z));v.co=center+(v.co-center)*(1-.20*fade)
