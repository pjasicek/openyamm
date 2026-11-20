"""Give the open mantle/panels a 1.5 mm lining, reserving a low-density strip of the body atlas."""
from pathlib import Path
import bpy,bmesh,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/ready.blend'))
body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data);g=bm.verts.layers.int['garment'];uv=bm.loops.layers.uv['UVMap'];head=bm.faces.layers.int['head']
outer=[f for f in bm.faces if all(v[g] in (1,5,6) for v in f.verts)];old=set(bm.faces);oldverts=set(bm.verts)
assert len(outer)>500
bmesh.ops.solidify(bm,geom=outer,thickness=-.0015)
shell=set(bm.faces)-old
bmesh.ops.recalc_face_normals(bm,faces=outer+list(shell))
# Solidify keeps the input faces on the offset inner shell and creates its outer cap.
assert sum(len(f.verts)==3 for f in shell)==len(outer)
inner=set(outer)|{f for f in shell if len(f.verts)!=3}
for f in bm.faces:
 if f[head]:continue
 for l in f.loops:
  l[uv].uv.x=l[uv].uv.x*(.25 if f in inner else .75)+(.75 if f in inner else 0)
for v in set(bm.verts)-oldverts:v[g]=12
bm.to_mesh(body.data);bm.free();body.data.update()
# Runtime skinning uses four influences; make that exact in the editable master too.
dropped=0
for v in body.data.vertices:
 weights=sorted([(e.group,e.weight) for e in v.groups if e.weight>1e-8],key=lambda x:-x[1]);keep=weights[:4];total=sum(w for _,w in keep);assert total>0
 dropped=max(dropped,sum(w for _,w in weights[4:]))
 for gi,w in weights:body.vertex_groups[gi].remove([v.index])
 for gi,w in keep:body.vertex_groups[gi].add([v.index],w/total,'REPLACE')
report={'outer_faces':len(outer),'new_lining_and_rim_faces':len(inner),'max_removed_weight':dropped,'body_triangles':sum(len(f.vertices)-2 for f in body.data.polygons)}
(p/'work/lining.json').write_text(json.dumps(report,indent=2));print(report)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/ready_lined.blend'))
