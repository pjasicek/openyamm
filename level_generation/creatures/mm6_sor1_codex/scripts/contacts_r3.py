"""Ray-verified signed distances for closed contact surfaces and a small rest-shape cloth fit."""
import bpy,bmesh,numpy as np,json
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

def inside(tree,point):
 votes=0
 for direction in [Vector((1,.173,.317)).normalized(),Vector((.291,1,.419)).normalized(),Vector((.137,.241,1)).normalized()]:
  start=point.copy();hits=0
  for count in range(32):
   q,n,ix,d=tree.ray_cast(start,direction,5)
   if q is None:break
   hits+=1;start=q+direction*1e-5
  votes+=hits%2
 return votes>=2

def solid_depth(tree,points,limit=.05):
 best=(0,None)
 for ix,pt in points:
  loc,n,fi,d=tree.find_nearest(pt,limit)
  if loc is not None and d>best[0] and inside(tree,pt):best=(d,ix)
 return best

def selfcheck():
 bm=bmesh.new();bmesh.ops.create_cube(bm,size=2);bm.verts.ensure_lookup_table();tree=BVHTree.FromBMesh(bm)
 assert inside(tree,Vector((0,0,0))) and not inside(tree,Vector((3,0,0)))
 assert abs(solid_depth(tree,[(0,Vector((.5,0,0)))],2)[0]-.5)<1e-6
 bm.free()
selfcheck()
