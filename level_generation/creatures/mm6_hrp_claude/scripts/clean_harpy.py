"""Repair confirmed wing holes, then measure hand digit separation and retain all native components."""
import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));o=bpy.data.objects['Body'];me=o.data
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();layer=bm.verts.layers.int.get('part')
boundary=[e for e in bm.edges if e.is_boundary];seen=set();filled=[]
for e in boundary:
 if e in seen:continue
 todo=[e];es=[];vs=set()
 while todo:
  q=todo.pop()
  if q in seen:continue
  seen.add(q);es.append(q);vs.update(q.verts)
  for v in q.verts:todo.extend(x for x in v.link_edges if x.is_boundary and x not in seen)
 c=np.array([v.co[:] for v in vs]);center=c.mean(0)
 if abs(center[0])>.18 and center[2]>1.08 and all(v[layer] in [0,1] for v in vs) and len(vs)>2:
  new=bmesh.ops.holes_fill(bm,edges=es,sides=0)['faces'];filled.append({'center':center.tolist(),'faces':len(new)})
  if new:bmesh.ops.triangulate(bm,faces=new)
bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
co=np.array([v.co[:] for v in me.vertices]);parts=np.array([v.value for v in me.attributes['part'].data]);E=np.array([e.vertices[:] for e in me.edges])
me.calc_loop_triangles();np.savez(P/'work/geometry_clean.npz',co=co,parts=parts,edges=E,tri=np.array([t.vertices[:] for t in me.loop_triangles]))
left=np.where(parts==1)[0];tree=kdtree.KDTree(len(left))
for i in left:tree.insert(Vector((-co[i,0]-.02,co[i,1],co[i,2])),int(i))
tree.balance();wing=parts==1
for i in np.where((co[:,0]<-.05)&(co[:,2]>1.08))[0]:
 if tree.find(Vector(co[i]))[2]<.045:wing[i]=True
np.save(P/'work/wing_mask.npy',wing)
adj=[[] for _ in co]
for a,b in E:adj[a].append(int(b));adj[b].append(int(a))
def comps(mask):
 remain=set(np.where(mask)[0]);out=[]
 while remain:
  v=remain.pop();todo=[v];ids=[]
  while todo:
   v=todo.pop();ids.append(v)
   for j in adj[v]:
    if j in remain:remain.remove(j);todo.append(j)
  if len(ids)>=5:out.append(ids)
 return sorted(out,key=len,reverse=True)
for side,sg in [('L',1),('R',-1)]:
 print('DIGIT CUT',side)
 for z in np.arange(.84,.65,-.01):
  groups=comps((co[:,0]*sg>.44)&(co[:,2]<z)&(co[:,2]>.60)&(~wing))
  print(round(z,3),[(len(g),np.round(co[g].mean(0),3).tolist()) for g in groups])
print('REPAIRED',filled,'TRIS',len(me.loop_triangles))
(P/'work/geometry_repairs.json').write_text(json.dumps({'filled_wing_holes':filled,'triangles':len(me.loop_triangles)},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/clean.blend'))
