"""Weld only coincident GLB seam vertices, keeping all per-corner UVs."""
from pathlib import Path
import bpy,bmesh,sys,json,numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/head_return.blend'))
head=next(o for o in bpy.data.objects if o.type=='MESH');head.name='HeadSource'
bm=bmesh.new();bm.from_mesh(head.data);before=len(bm.verts);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
report={'vertices_before':before,'vertices_after':len(bm.verts),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)}
bm.to_mesh(head.data);bm.free()
for f in head.data.polygons:f.use_smooth=True
if head.data.has_custom_normals:
 with bpy.context.temp_override(object=head):bpy.ops.mesh.customdata_custom_splitnormals_clear()
co=np.array([tuple(v.co) for v in head.data.vertices]);lo=co.min(0);hi=co.max(0)
(p/'work/head_weld.json').write_text(json.dumps(report,indent=2));print('HEAD_WELD',report)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_weld.blend'))
for tex in [True,False]:
 common.workbench_clay(bpy.context.scene,textured=tex)
 common.render_views(str(p/'review'/('head_weld_texture' if tex else 'head_weld_clay')),float((lo[2]+hi[2])/2),float(np.ptp(co,axis=0).max()*1.1),views=('front','left','back','three_quarter'),resolution=(650,650),target=tuple((lo[:2]+hi[:2])/2))
