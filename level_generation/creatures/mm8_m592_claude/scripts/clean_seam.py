"""Remove only the tiny centre-plane intersections left by the anatomical symmetry repair."""
from pathlib import Path
import bpy,bmesh,json,numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));o=bpy.data.objects['Body'];before=len(o.data.vertices)
bm=bmesh.new();bm.from_mesh(o.data);seam=[v for v in bm.verts if abs(v.co.x)<.0002]
bmesh.ops.remove_doubles(bm,verts=seam,dist=.0008)
bmesh.ops.dissolve_degenerate(bm,edges=[e for e in bm.edges if all(abs(v.co.x)<.0002 for v in e.verts)],dist=.0001)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
co=np.array([tuple(v.co) for v in o.data.vertices]);o.data.attributes['orig_co'].data.foreach_set('vector',co.ravel())
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
report={'before_vertices':before,'after_vertices':len(co),'scope':'Only x=0 symmetry seam; weld within 0.8 mm and dissolve sub-0.1 mm seam edges. No whole-body weld or surface smoothing.'};(P/'review/geometry/seam_cleanup.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
