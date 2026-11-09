"""Replace the folded front trouser patch revealed by the male pilot; preserve submitted files."""
import bpy,bmesh,sys,os,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/male/rig_weighted_v1.blend'))
b=bpy.data.objects['Body'];m=b.data;bm=bmesh.new();bm.from_mesh(m)
pc=bm.verts.layers.int['piece'];fp=bm.faces.layers.int['source_piece']
old_edges={e for e in bm.edges if e.is_boundary};original=len(bm.faces)
faces=[f for f in bm.faces if f[fp]==2 and any(-.14<v.co.x<.14 and .70<v.co.z<.975 and v.co.y<-.02 for v in f.verts)]
assert 60<len(faces)<350,len(faces)
bmesh.ops.delete(bm,geom=faces,context='FACES')
boundary=[e for e in bm.edges if e.is_boundary and e not in old_edges]
assert len(boundary)>15
# Include pre-existing waist edges only when they belong to the opened patch loop.
new_boundary=set(boundary);all_boundary={e for e in bm.edges if e.is_boundary}
loops=[]
while all_boundary:
 todo=[next(iter(all_boundary))];edges=set()
 while todo:
  e=todo.pop()
  if e not in all_boundary:continue
  all_boundary.remove(e);edges.add(e)
  todo.extend(q for v in e.verts for q in v.link_edges if q in all_boundary)
 if edges & new_boundary:loops.append(edges)
new=[]
for loop in loops:
 degree={v:sum(e in loop for e in v.link_edges) for v in {v for e in loop for v in e.verts}}
 print('PATCH_LOOP',len(loop),'degrees',[n for n in degree.values() if n!=2],flush=True)
 assert all(n==2 for n in degree.values())
 res=bmesh.ops.holes_fill(bm,edges=list(loop),sides=0)
 new.extend(bmesh.ops.triangulate(bm,faces=res['faces'],quad_method='BEAUTY',ngon_method='BEAUTY')['faces'])
for f in new:
 f[fp]=2;f.material_index=0;f.smooth=True
 if f.normal.y>0:f.normal_flip()
 for v in f.verts:v[pc]=2
bm.normal_update()
print('PATCH',len(faces),len(boundary),len(new),flush=True)
assert not [e for e in boundary if e.is_boundary]
# The concave crotch can choose an existing back-shell edge as a fill diagonal; rotate only the new diagonal.
for e in list(bm.edges):
 if len(e.link_faces)<=2:continue
 pair=[f for f in e.link_faces if f in new]
 assert len(e.link_faces)==4 and len(pair)==2
 a,b=e.verts;c=next(v for v in pair[0].verts if v not in (a,b));d=next(v for v in pair[1].verts if v not in (a,b))
 normal=(pair[0].normal+pair[1].normal).normalized()
 bmesh.ops.delete(bm,geom=pair,context='FACES_ONLY')
 for verts in ((c,a,d),(c,d,b)):
  f=bm.faces.new(verts);f[fp]=2;f.material_index=0;f.smooth=True
  f.normal_update()
  if f.normal.dot(normal)<0:f.normal_flip()
 new=[f for f in new if f.is_valid]
bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
assert not [e for e in bm.edges if not e.is_manifold and not e.is_boundary]
assert all(f.calc_area()>1e-10 for f in bm.faces)
report={'removed_faces':len(faces),'replacement_triangles':len(bm.faces)-(original-len(faces)),'triangles_before':original,'triangles_after':len(bm.faces),'region':'front trouser patch; existing boundary and its weights retained','old_boundaries':len(old_edges),'new_boundaries':sum(e.is_boundary for e in bm.edges)}
assert report['new_boundaries']<=report['old_boundaries']
bm.to_mesh(m);bm.free();m.update()
# The patch triangles reuse the weighted boundary; no empty or detached vertices may remain.
assert all(v.groups for v in m.vertices)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/male/rig_weighted_v2.blend'))
(P/'review/male/trouser_repair.json').write_text(json.dumps(report,indent=2)+'\n')
print('TROUSER',report,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
