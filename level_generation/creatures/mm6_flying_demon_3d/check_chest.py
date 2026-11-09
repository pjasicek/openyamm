"""Check actual torso triangle intersections before paid texturing."""
from pathlib import Path
import bpy,json
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_uv_master.blend'))
body=bpy.context.scene.objects['Flying_Demon_Body'];m=body.data
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def hit(a,b,t):
 d=sub(b,a);e1=sub(t[1],t[0]);e2=sub(t[2],t[0]);h=cross(d,e2);det=dot(e1,h)
 if abs(det)<1e-14:return False
 s=sub(a,t[0]);u=dot(s,h)/det;q=cross(s,e1);v=dot(d,q)/det;time=dot(e2,q)/det
 return 1e-5<u and 1e-5<v and u+v<1-1e-5 and 1e-5<time<1-1e-5
# Independent jaw, eyes and teeth meet the body by design; test the continuous torso shell.
adj=[set() for v in m.vertices]
for edge in m.edges:
 a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
unseen=set(range(len(m.vertices)));components=[]
while unseen:
 seed=unseen.pop();part={seed};todo=[seed]
 while todo:
  for n in adj[todo.pop()]:
   if n in unseen:unseen.remove(n);part.add(n);todo.append(n)
 components.append(part)
principal=max(components,key=len)
shell={f.index for f in m.polygons if set(f.vertices)<=principal}
region={f.index for f in m.polygons if f.index in shell and f.material_index==0 and abs(f.center.x)<.25 and 1.12<f.center.z<1.54 and f.center.y<-.14}
tree=BVHTree.FromPolygons([v.co for v in m.vertices],[list(f.vertices) for f in m.polygons],all_triangles=True)
pairs={(min(a,b),max(a,b)) for a,b in tree.overlap(tree) if a!=b and a in shell and b in shell and (a in region or b in region) and m.polygons[a].material_index==m.polygons[b].material_index==0}
bad=[]
for i,j in pairs:
 a=[m.vertices[v].co for v in m.polygons[i].vertices];b=[m.vertices[v].co for v in m.polygons[j].vertices]
 if any(hit(a[k],a[(k+1)%3],b) or hit(b[k],b[(k+1)%3],a) for k in range(3)):bad.append((i,j))
report={'status':'pass' if not bad else 'fail','scope':'principal continuous body shell; independent jaw/eyes/teeth excluded', 'torso_faces':len(region),'tested_candidate_pairs':len(pairs),'interior_skin_triangle_crossings':len(bad),'crossings':bad}
(P/'review/chest_surface_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:v for k,v in report.items() if k!='crossings'},flush=True);assert not bad
