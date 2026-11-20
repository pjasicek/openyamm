"""Recover head geometry from Meshy's preserved dense source; reject the damaged remesh."""
from pathlib import Path
import bpy,bmesh,numpy as np,sys,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
common.clear_scene();bpy.ops.import_scene.gltf(filepath=str(p/'meshy/head_geometry_v1/model_urls_pre_remeshed_glb.glb'))
head=next(o for o in bpy.data.objects if o.type=='MESH');head.name='HeadSource'
for x in bpy.data.objects:x.select_set(x is head)
bpy.context.view_layer.objects.active=head;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
tri=sum(len(f.vertices)-2 for f in head.data.polygons);print('SOURCE_TRIANGLES',tri,flush=True)
mod=head.modifiers.new('Preserve dense source shape','DECIMATE');mod.ratio=80000/tri;bpy.ops.object.modifier_apply(modifier=mod.name)
print('REDUCED_INTERMEDIATE',len(head.data.vertices),flush=True)
for f in head.data.polygons:f.use_smooth=True
if head.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
bm=bmesh.new();bm.from_mesh(head.data)
report={'source_triangles':tri,'triangles':sum(len(f.vertices)-2 for f in head.data.polygons),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)};bm.free();print('HEAD_RECOVER',report,flush=True)
co=np.array([tuple(v.co) for v in head.data.vertices]);lo=co.min(0);hi=co.max(0)
(p/'work/head_recovered.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_recovered.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/head_recovered'),float((lo[2]+hi[2])/2),float(np.ptp(co,axis=0).max()*1.1),views=('front','left','back','three_quarter'),resolution=(650,650),target=tuple((lo[:2]+hi[:2])/2))
