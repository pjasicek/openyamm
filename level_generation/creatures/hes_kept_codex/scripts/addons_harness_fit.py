"""Fit continuous straps to the convex torso cross-section; rays through shirt openings gave inward notches."""
import bpy,sys,os,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];b=bpy.data.objects['Kept'];o=bpy.data.objects['hes_kept_plate'];r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
pc=[v.value for v in b.data.attributes['piece'].data];adj={v.index:set()for v in o.data.vertices}
for e in o.data.edges:a,c=e.vertices;adj[a].add(c);adj[c].add(a)
unseen=set(adj);components=[]
while unseen:
 part={unseen.pop()};todo=list(part)
 while todo:
  for j in adj[todo.pop()]-part:part.add(j);todo.append(j)
 unseen-=part;components.append(part)
def hull(z):
 pts=[]
 for e in b.data.edges:
  a,c=[b.data.vertices[i].co for i in e.vertices]
  if pc[e.vertices[0]]not in (0,1) or (a.z-z)*(c.z-z)>0 or abs(a.z-c.z)<1e-8:continue
  p=a.lerp(c,(z-a.z)/(c.z-a.z))
  if abs(p.x+.03255)<.205:pts.append((float(p.x),float(p.y)))
 pts=sorted(set(pts));cross=lambda a,c,d:(c[0]-a[0])*(d[1]-a[1])-(c[1]-a[1])*(d[0]-a[0]);lo=[];hi=[]
 for q in pts:
  while len(lo)>1 and cross(lo[-2],lo[-1],q)<=0:lo.pop()
  lo.append(q)
 for q in reversed(pts):
  while len(hi)>1 and cross(hi[-2],hi[-1],q)<=0:hi.pop()
  hi.append(q)
 return lo[:-1]+hi[:-1]
def cross(a,c):return a.x*c.y-a.y*c.x
report=[]
for ids in components:
 zs=[o.data.vertices[i].co.z for i in ids];z=(max(zs)+min(zs))*.5
 if len(ids)!=128 or min(abs(z-v)for v in (1.16,1.34))>.01:continue
 z=min((1.16,1.34),key=lambda v:abs(v-z));ring=[]
 # Recover each ring's angular station and the inner/outer side from its original mesh ordering.
 for i in ids:
  v=o.data.vertices[i];p=v.co;dz=-.0135 if p.z<z else .0135;angle=round(math.atan2(p.y-.022,p.x+.03255)/(math.tau/32))*(math.tau/32);direction=Vector((math.cos(angle),math.sin(angle)));centre=Vector((-.03255,.022));H=hull(z+dz);hits=[]
  for aa,bb in zip(H,H[1:]+H[:1]):
   a=Vector(aa)-centre;edge=Vector(bb)-Vector(aa);den=cross(direction,edge)
   if abs(den)<1e-8:continue
   radius=cross(a,edge)/den;t=cross(a,direction)/den
   if radius>0 and -1e-6<=t<=1+1e-6:hits.append(radius)
  assert hits,(z,angle);ring.append((i,angle,dz,min(hits),math.hypot(p.x+.03255,p.y-.022)))
 for i,angle,dz,rad,old in ring:
  paired=sorted([x for x in ring if abs(x[1]-angle)<1e-5 and x[2]==dz],key=lambda x:x[4]);gap=.009 if paired[0][0]==i else .014
  o.data.vertices[i].co=Vector((-.03255+math.cos(angle)*(rad+gap),.022+math.sin(angle)*(rad+gap),z+dz))
 report.append({'height':z,'vertices':len(ids)})
assert len(report)==2,report
bpy.ops.wm.save_as_mainfile(filepath=str(path));(P/'review/addons_v2/harness_fit.json').write_text(json.dumps(report,indent=2)+'\n');print('HARNESS_ENVELOPE',report,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
