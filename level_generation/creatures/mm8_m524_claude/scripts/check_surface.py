import bpy,bmesh,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
o=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(o.data)
report={'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'vertices':len(bm.verts),'faces':len(bm.faces)}
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
(P/'work/surface_check.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/surface_v1.blend'))
