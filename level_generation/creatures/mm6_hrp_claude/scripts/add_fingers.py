"""Restore the fifth hand digit omitted by Smart Topology, using its existing finger surface."""
import bpy,bmesh,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/clean.blend'));body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);adj=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
added=[]
for sd,sg,cut,newpart in [('L',1,.80,8),('R',-1,.82,9)]:
 remain=set(np.where((co[:,0]*sg>.51)&(co[:,2]<cut)&(co[:,2]>.6))[0]);groups=[]
 while remain:
  start=remain.pop();todo=[start];ids=[]
  while todo:
   a=todo.pop();ids.append(a)
   for b in adj[a]:
    if b in remain:remain.remove(b);todo.append(b)
  if len(ids)>12:groups.append(ids)
 assert len(groups)==3,(sd,[len(g) for g in groups])
 groups.sort(key=lambda g:co[g,1].mean());ids=groups[1];idsset=set(ids);mapping={old:i for i,old in enumerate(ids)}
 faces=[[mapping[i] for i in f.vertices] for f in me.polygons if all(i in idsset for i in f.vertices)]
 c=co[ids].copy();base=c[c[:,2]>cut-.016].mean(0);c[:,0]=base[0]+(c[:,0]-base[0])*.82+sg*.004;c[:,1]=base[1]+(c[:,1]-base[1])*.74-.029;c[:,2]=cut+(c[:,2]-cut)*.92
 mesh=bpy.data.meshes.new(sd+'RingFinger');mesh.from_pydata(c.tolist(),[],faces);mesh.update()
 bm=bmesh.new();bm.from_mesh(mesh);edges=[e for e in bm.edges if e.is_boundary];out=bmesh.ops.extrude_edge_only(bm,edges=edges)
 ext=[v for v in out['geom'] if isinstance(v,bmesh.types.BMVert)]
 for v in ext:v.co.z+=.040
 cap=[e for e in bm.edges if e.is_boundary];bmesh.ops.holes_fill(bm,edges=cap,sides=0);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 attr=mesh.attributes.new('part','INT','POINT');attr.data.foreach_set('value',np.full(len(mesh.vertices),newpart,dtype=np.int32));obj=bpy.data.objects.new(sd+'RingFinger',mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(me.materials[0]);added.append({'side':sd,'new_part':newpart,'vertices':len(mesh.vertices),'source_piece':list(map(int,ids))})
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
for f in body.data.polygons:f.use_smooth=True
co=np.array([v.co[:] for v in body.data.vertices]);parts=np.array([v.value for v in body.data.attributes['part'].data]);body.data.calc_loop_triangles()
np.savez(P/'work/geometry_rig.npz',co=co,parts=parts,edges=np.array([e.vertices[:] for e in body.data.edges]),tri=np.array([t.vertices[:] for t in body.data.loop_triangles]))
wing=np.load(P/'work/wing_mask.npy')[:len(me.vertices)];wing=np.r_[wing,np.zeros(len(co)-len(wing),dtype=bool)];np.save(P/'work/wing_mask.npy',wing)
(P/'work/finger_repair.json').write_text(json.dumps(added,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anatomy.blend'));print('Added one separate ring finger per hand;',len(body.data.loop_triangles),'triangles')
