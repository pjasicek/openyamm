"""Place a horizontal weapon on an actual lower-hull support segment."""
import math
from mathutils import Matrix,Vector


def rest_weapon(objects):
 points=sorted(set((round(v.co.y,8),round(v.co.z,8)) for o in objects for v in o.data.vertices));hull=[]
 for point in points:
  while len(hull)>1 and (hull[-1][0]-hull[-2][0])*(point[1]-hull[-1][1])-(hull[-1][1]-hull[-2][1])*(point[0]-hull[-1][0])<=0:hull.pop()
  hull.append(point)
 supports=[(b[0]-a[0],a,b) for a,b in zip(hull,hull[1:]) if b[0]-a[0]>.05 and abs(math.atan2(b[1]-a[1],b[0]-a[0]))<math.radians(18)]
 assert supports,'No plausible longitudinal support; inspect the weapon orientation'
 _,a,b=max(supports);angle=-math.atan2(b[1]-a[1],b[0]-a[0]);rotation=Matrix.Rotation(angle,3,'X')
 for obj in objects:
  for vertex in obj.data.vertices:vertex.co=rotation@vertex.co
 points=[v.co.copy() for o in objects for v in o.data.vertices];lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)]);shift=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
 for obj in objects:
  for vertex in obj.data.vertices:vertex.co-=shift
 assert abs(min(v.co.z for o in objects for v in o.data.vertices))<1e-6
 return {'support_pitch_degrees':math.degrees(angle),'support_span':b[0]-a[0]}
