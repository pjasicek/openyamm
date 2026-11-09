"""Inspect and fit the detailed head against the retained Mage body before joining it."""
from pathlib import Path
import bpy,bmesh,numpy as np,sys,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_body.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p/'meshy/head_model_v1/model_urls_glb.glb'))
new=set(bpy.data.objects)-before;heads=[o for o in new if o.type=='MESH'];assert heads
for o in bpy.data.objects:o.select_set(o in heads)
bpy.context.view_layer.objects.active=heads[0]
if len(heads)>1:bpy.ops.object.join()
head=bpy.context.object;head.name='HeadSource'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co) for v in head.data.vertices]);lo=co.min(0);hi=co.max(0);scale=.40/(hi[2]-lo[2])
offset=Vector((-.018-(lo[0]+hi[0])*.5*scale,-.235-lo[1]*scale,1.70-hi[2]*scale))
for v in head.data.vertices:v.co=v.co*scale+offset
head.data.update()
body.hide_render=True;common.workbench_clay(bpy.context.scene,textured=True)
common.render_views(str(p/'review/geometry/head_return'),1.50,.50,views=('front','left','back','three_quarter'),resolution=(600,600),target=(-.018,-.02))
body.hide_render=False
# Hide the old head only in the inspection copy; keep the authoritative body checkpoint untouched.
bm=bmesh.new();bm.from_mesh(body.data);pv=bm.verts.layers.int['piece']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pv] in [6,7,8,11,12] or (v[pv]==0 and v.co.z>1.36)],context='VERTS');bm.to_mesh(body.data);bm.free()
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/geometry/head_fit'),.85,2.5,views=('front','left','three_quarter'),resolution=(600,900))
# Save only the fitted source separately, leaving the body available from rig_body.
for o in bpy.data.objects:
 if o is not head:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_fitted.blend'))
report={'source_bounds':[lo.tolist(),hi.tolist()],'scale':float(scale),'offset':list(offset),'triangles':sum(len(f.vertices)-2 for f in head.data.polygons)}
(p/'review/geometry/head_fit.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
