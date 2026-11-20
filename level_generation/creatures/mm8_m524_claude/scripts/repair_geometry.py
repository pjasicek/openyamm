"""Remove the duplicate middle finger per hand; close only measured accidental skin holes."""
import bpy,bmesh,json,heapq
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/surface_v1.blend'))
o=bpy.data.objects['Body'];me=o.data
c=np.array([v.co[:] for v in me.vertices]);adj=[[] for _ in c]
for e in me.edges:
 a,b=e.vertices;adj[a].append(int(b));adj[b].append(int(a))
remove=set();reports=[]
for sign in [1,-1]:
 allowed=set(np.where((c[:,0]*sign>.6)&(c[:,2]<.88)&(c[:,2]>.45)&(c[:,1]<.7))[0])
 low=set(v for v in allowed if c[v,2]<.75);parts=[]
 while low:
  todo=[low.pop()];ids=[]
  while todo:
   v=todo.pop();ids.append(v)
   for w in adj[v]:
    if w in low:low.remove(w);todo.append(w)
  if len(ids)>10:parts.append(ids)
 assert len(parts)==4,(sign,[len(x) for x in parts])
 tips=[ids[int(np.argmin(c[ids,2]))] for ids in parts]
 scores=[]
 for seed in tips:
  dist=np.full(len(c),1e9);dist[seed]=0.;q=[(0.,seed)]
  while q:
   d,v=heapq.heappop(q)
   if d>dist[v]+1e-9:continue
   for w in adj[v]:
    if w not in allowed:continue
    nd=d+float(np.linalg.norm(c[w]-c[v]))
    if nd<dist[w]:dist[w]=nd;heapq.heappush(q,(nd,w))
  scores.append(dist)
 owner=np.argmin(scores,axis=0);middle=min(range(4),key=lambda k:c[tips[k],2])
 ids=[v for v in allowed if owner[v]==middle and c[v,2]<.82]
 remove.update(ids);reports.append({'side':sign,'removed_tip':c[tips[middle]].tolist(),'removed_vertices':len(ids)})
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[bm.verts[i] for i in sorted(remove)],context='VERTS')
# Four accidental skin openings and the two cut finger roots; preserve the separate tooth root opening.
left=set(e for e in bm.edges if e.is_boundary);loops=[]
while left:
 edge=left.pop();todo=[edge];group=[]
 while todo:
  e=todo.pop();group.append(e)
  for v in e.verts:
   for n in v.link_edges:
    if n in left:left.remove(n);todo.append(n)
 loops.append(group)
for edges in loops:
 vs=list({v for e in edges for v in e.verts});pts=np.array([v.co[:] for v in vs]);center=pts.mean(0)
 tooth=(center[1]<0 and center[2]>1.65 and abs(center[0])<.08)
 if not tooth:
  if len(edges)==5:
   # Smart Topology left crossed boundary loops; replace their one-ring patch, not the whole surface.
   faces={f for v in vs for f in v.link_faces}
   outer={e for f in faces for e in f.edges if sum(n in faces for n in e.link_faces)==1 and not e.is_boundary}
   bmesh.ops.delete(bm,geom=list(faces),context='FACES')
   edges=[e for e in outer if e.is_valid and e.is_boundary]
  result=bmesh.ops.holes_fill(bm,edges=edges,sides=0)
  assert result['faces'],(len(edges),center.tolist())
  bmesh.ops.triangulate(bm,faces=result['faces'])
assert sum(e.is_boundary for e in bm.edges)==11,sum(e.is_boundary for e in bm.edges)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
bpy.context.view_layer.objects.active=o;o.select_set(True)
if me.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
for f in me.polygons:f.material_index=0;f.use_smooth=True
me.calc_loop_triangles();co=np.array([v.co[:] for v in me.vertices]);edges=np.array([e.vertices[:] for e in me.edges]);tri=np.array([t.vertices[:] for t in me.loop_triangles])
assert np.isfinite(co).all() and len(tri)>14000
np.savez(P/'work/geometry_repaired.npz',co=co,edges=edges,tri=tri)
(P/'work/geometry_repairs.json').write_text(json.dumps({'finger_correction':reports,'triangles':len(tri),'remaining_open_tooth_root':True},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_repaired.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.world=bpy.data.worlds.new('World');sc.world.color=(.13,.13,.15);sc.render.resolution_x=sc.render.resolution_y=850;sc.render.resolution_percentage=100
from mathutils import Vector
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,pos,target,scale in [('front',(0,-6,1.1),(0,0,1.1),2.4),('quarter',(4,-6,3),(0,.7,1),4.2),('side',(6,1.5,1),(0,1.5,1),4.4),('hand_left',(3,-4,1.4),(.88,.24,.78),.7),('hand_right',(-3,-4,1.4),(-.88,.24,.78),.7)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(P/'review'/f'repaired_{name}.png');bpy.ops.render.render(write_still=True)
print(json.dumps(reports))
