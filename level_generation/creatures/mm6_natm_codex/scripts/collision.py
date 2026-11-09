from mathutils import Vector
RAYS=[Vector(d).normalized() for d in [(1,.173,.231),(-.231,1,.173),(.173,-.231,1)]]
def inside(tree,p):
 votes=0
 for direction in RAYS:
  origin=p+direction*.000003;count=0
  for _ in range(30):
   hit,n,idx,dist=tree.ray_cast(origin,direction,5.0)
   if hit is None:break
   count+=1;origin=hit+direction*.00002
  votes+=count%2
 return votes>=2
def penetration(tree,points):
 worst=0;where=None
 for p in points:
  q,n,idx,d=tree.find_nearest(Vector(p))
  if q is not None and (Vector(p)-q).dot(n)<-.00001 and d>worst and inside(tree,Vector(p)):worst=d;where=p.tolist()
 return worst,where
