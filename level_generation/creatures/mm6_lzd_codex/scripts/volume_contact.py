"""Reject nearest-plane contacts outside the struck component's enclosing box."""
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def volumes(vertices,faces,pieces):
 xyz=np.asarray(vertices,float);groups={}
 for face in faces:groups.setdefault(int(pieces[face[0]]),[]).append(list(face))
 result=[]
 for piece,polys in groups.items():
  ids=sorted({i for face in polys for i in face});points=xyz[ids];center=points.mean(0);_,_,axes=np.linalg.svd(points-center,full_matrices=False)
  if axes.shape!=(3,3):continue
  projected=(points-center)@axes.T;lo=projected.min(0);hi=projected.max(0)
  assert np.all(projected>=lo-1e-8)and np.all(projected<=hi+1e-8)
  result.append((piece,center,axes,lo,hi,xyz,polys))
 return result
def deepest(items,points,limit=.05):
 points=np.asarray(points,float).reshape(-1,3);worst=(0,None,None)
 for piece,center,axes,lo,hi,xyz,polys in items:
  local=(points-center)@axes.T;inside=np.all((local>=lo-1e-6)&(local<=hi+1e-6),axis=1)
  if not inside.any():continue
  tree=BVHTree.FromPolygons(xyz.tolist(),polys)
  for point in points[inside]:
   p=Vector(point);loc,n,_,d=tree.find_nearest(p,limit)
   if loc is not None and d>worst[0]and(p-loc).dot(n)<-.7*d:
    votes=0
    for direction in [Vector((.891,.321,.324)).normalized(),Vector((-.217,.912,.349)).normalized(),Vector((.411,-.231,.882)).normalized()]:
     origin=p.copy();crossings=0
     for _ in range(128):
      hit,_,_,distance=tree.ray_cast(origin,direction)
      if hit is None:break
      crossings+=1;origin=hit+direction*2e-6
     votes+=crossings%2
    if votes>=2:worst=(d,piece,point.tolist())
 return worst
def self_test():
 xyz=np.array([[x,y,z]for x in [-1,1]for y in [-1,1]for z in [-.001,.001]],float)
 faces=[[0,4,6,2],[1,3,7,5],[0,1,5,4],[2,6,7,3],[0,2,3,1],[4,5,7,6]]
 # Enclosing boxes cannot classify a point four centimetres behind a 2 mm plate as inside it.
 items=volumes(xyz,[f[::-1]for f in faces],np.zeros(8,int))
 assert deepest(items,[[0,0,.04]])[0]==0
 assert deepest(items,[[0,0,0]])[0]>.0009
self_test()
