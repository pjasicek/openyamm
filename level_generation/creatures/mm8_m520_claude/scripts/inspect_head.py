"""Inspect the untouched dedicated Meshy head, retaining original materials and UVs."""
from pathlib import Path
import bpy,bmesh,numpy as np,sys,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
common.clear_scene();bpy.ops.import_scene.gltf(filepath=str(p/'meshy/head_geometry_v1/model_urls_glb.glb'))
heads=[o for o in bpy.data.objects if o.type=='MESH']
for o in heads:
 for x in bpy.data.objects:x.select_set(x is o)
 bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co) for o in heads for v in o.data.vertices]);lo=co.min(0);hi=co.max(0)
report={'bounds':[lo.tolist(),hi.tolist()],'meshes':[]}
for o in heads:
 bm=bmesh.new();bm.from_mesh(o.data)
 report['meshes'].append({'name':o.name,'vertices':len(o.data.vertices),'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),'uv_sets':[u.name for u in o.data.uv_layers],'materials':[m.name for m in o.data.materials]});bm.free()
 for f in o.data.polygons:f.use_smooth=True
(p/'work/head_return.json').write_text(json.dumps(report,indent=2));print('HEAD_RETURN',json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_return.blend'))
for tex in [True,False]:
 common.workbench_clay(bpy.context.scene,textured=tex)
 common.render_views(str(p/'review'/('head_return_texture' if tex else 'head_return_clay')),float((lo[2]+hi[2])/2),float(np.ptp(co,axis=0).max()*1.1),views=('front','left','back','right','three_quarter'),resolution=(650,650),target=tuple((lo[:2]+hi[:2])/2))
