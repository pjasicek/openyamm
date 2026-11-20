"""Inside a possibly open skinned body: majority parity avoids treating empty space beside thin cloth as solid."""
from mathutils import Vector
DIRECTIONS=[Vector((1,.371,.193)).normalized(),Vector((.217,1,.413)).normalized(),Vector((.317,.271,1)).normalized()]
def inside(tree,p):
 votes=0
 for direction in DIRECTIONS:
  q=Vector(p)+direction*1e-5;count=0
  for _ in range(64):
   loc,normal,face,distance=tree.ray_cast(q,direction,3)
   if loc is None:break
   count+=1;q=loc+direction*1e-5
  votes+=count%2
 return votes>=2
