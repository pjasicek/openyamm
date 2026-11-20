import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_native.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['Crossbow'];a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(37)
inv=(rig.matrix_world@rig.pose.bones['Crossbow'].matrix@rig.data.bones['Crossbow'].matrix_local.inverted()).inverted()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pts=np.array([tuple(inv@body.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear()
pv=np.array([v.value for v in body.data.attributes['piece'].data]);fv=np.array([v.value for v in body.data.attributes['finger'].data]);weapon=np.array([v.co[:] for v in prop.data.vertices]);adj=[set() for _ in weapon]
for e in prop.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
components=[];seen=set()
for i in range(len(weapon)):
 if i in seen:continue
 todo=[i];part=set()
 while todo:
  v=todo.pop()
  if v in part:continue
  part.add(v);todo.extend(adj[v]-part)
 seen|=part;faces=[tuple(p.vertices) for p in prop.data.polygons if p.vertices[0] in part];c=weapon[list(part)]
 components.append((BVHTree.FromPolygons(weapon.tolist(),faces),c.min(0),c.max(0)))
def penetration(p):
 worst=0
 for tree,lo,hi in components:
  for q in p[np.all(p>=lo,1)&np.all(p<=hi,1)]:
   loc,norm,face,d=tree.find_nearest(Vector(q))
   if (Vector(q)-loc).dot(norm)<-1e-5:worst=max(worst,d)
 return worst
out={}
for s,pi in [('R',8),('L',7)]:
 hand=pts[pv==pi];results=[]
 for az in range(0,360,15):
  for el in range(-90,91,15):
   d=np.array([math.cos(math.radians(az))*math.cos(math.radians(el)),math.sin(math.radians(az))*math.cos(math.radians(el)),math.sin(math.radians(el))])
   worst=max(penetration(hand+d*t) for t in np.arange(.002,.121,.004))
   results.append((worst,az,el,d.tolist()))
 results.sort();out[s]=results[:20];print('ESCAPE',s,results[:10],flush=True)
print('VERTEX FINGERS',[(i,int(pv[i]),int(fv[i])) for i in (2984,3242,4804,4870)],flush=True)
(P/'work/grip_escape.json').write_text(json.dumps(out,indent=2))
