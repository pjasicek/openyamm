"""Remove Meshy's extra rear digit on each hand; retain four fingers and one thumb."""
from pathlib import Path
import json
import numpy as np
import bpy
import bmesh
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
obj=bpy.data.objects['Body']; bm=bmesh.new();bm.from_mesh(obj.data)
bm.verts.ensure_lookup_table();co=np.array([v.co[:] for v in bm.verts]);original=list(bm.verts)
adj=[[] for _ in co]
for e in bm.edges:
 a,b=e.verts;adj[a.index].append(b.index);adj[b.index].append(a.index)
repairs=[]
for side in ['L','R']:
 d=json.loads((P/f'work/finger_candidates_{side}.json').read_text())
 k=max(range(len(d['fingers'])),key=lambda i:co[d['fingers'][i],1].mean())
 ids=d['fingers'][k];line=np.array(d['lines'][k]);tip=line[-1];base=line[1];axis=tip-base;axis/=np.linalg.norm(axis)
 protect=set(d['thumb'])|{v for i,c in enumerate(d['fingers']) if i!=k for v in c}
 seed=ids[np.argmax(co[ids]@axis)];best=None
 for back in np.arange(0,.075,.0025):
  q=base-axis*back;mask=(co-q)@axis>0;seen={seed};todo=[seed]
  while todo:
   v=todo.pop()
   for w in adj[v]:
    if mask[w] and w not in seen:seen.add(w);todo.append(w)
  if protect & seen or len(seen)>250:break
  best=(q,seen)
 assert best is not None
 q,seen=best
 # Cut only the faces of this finger and its boundary, keeping the rest of the body unchanged.
 faces={f for i in seen for f in original[i].link_faces};edges={e for f in faces for e in f.edges};verts={v for f in faces for v in f.verts}
 cut=bmesh.ops.bisect_plane(bm,geom=list(verts|edges|faces),plane_co=Vector(q),plane_no=Vector(axis),dist=1e-7)
 start=original[seed];todo=[start];remove={start}
 while todo:
  v=todo.pop()
  for e in v.link_edges:
   w=e.other_vert(v)
   if (w.co-Vector(q)).dot(Vector(axis))>1e-6 and w not in remove:remove.add(w);todo.append(w)
 assert not any(original[i] in remove for i in protect)
 boundary=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge)]
 bmesh.ops.delete(bm,geom=list(remove),context='VERTS')
 boundary=[e for e in boundary if e.is_valid and e.is_boundary]
 assert len(boundary)>=3
 cap=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)['faces']
 bmesh.ops.triangulate(bm,faces=cap)
 repairs.append({'side':side,'removed_vertices':len(remove),'cut':q.tolist(),'retained_fingers':4,'thumb':1})
bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
for f in obj.data.polygons:f.use_smooth=True
(P/'work/hand_repairs.json').write_text(json.dumps(repairs,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fitted_body.blend'))
print(repairs)
