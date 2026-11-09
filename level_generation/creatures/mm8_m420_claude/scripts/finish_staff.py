"""Verified UV carry-over, native staff proportions, then silhouette-preserving reduction."""
import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/staff_prepared.blend'));target=bpy.data.objects['StaffMesh'];before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/staff_retexture_v1/model_urls_glb.glb'));new=set(bpy.data.objects)-before
source=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.polygons));T=np.array([v.co[:] for v in target.data.vertices]);S=np.array([(source.matrix_world@v.co)[:] for v in source.data.vertices]);k=np.ptp(T,axis=0).max()/np.ptp(S,axis=0).max();S=S*k+(T.max(0)+T.min(0)-(S.max(0)+S.min(0))*k)*.5
assert len(source.data.polygons)==len(target.data.polygons)
tree=kdtree.KDTree(len(source.data.polygons))
for f in source.data.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
tree.balance();worst=0
for f in target.data.polygons:
 _,i,d=tree.find(Vector(T[list(f.vertices)].mean(0)));sf=source.data.polygons[i];worst=max(worst,d)
 for li,vi in zip(f.loop_indices,f.vertices):
  ds=np.linalg.norm(S[list(sf.vertices)]-T[vi],axis=1);j=int(ds.argmin());assert ds[j]<.00001,float(ds[j]);target.data.uv_layers.active.data[li].uv=source.data.uv_layers.active.data[sf.loop_indices[j]].uv
assert worst<.00001,worst
for o in new:bpy.data.objects.remove(o,do_unlink=True)
for v in target.data.vertices:v.co.z*=.75 if v.co.z<0 else 1.08
# Native front: body201px, staff roughly139px including diagonal projection; 24mm grip stays fixed.
for o in bpy.data.objects:o.select_set(o==target)
bpy.context.view_layer.objects.active=target
mod=target.modifiers.new('StaffSilhouetteBudget','DECIMATE');mod.ratio=1800/len(target.data.polygons);bpy.ops.object.modifier_apply(modifier=mod.name)
mod=target.modifiers.new('FrozenTriangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
assert all(len(f.vertices)==3 for f in target.data.polygons)
(P/'work/staff_final_geometry.json').write_text(json.dumps({'texture_uv_correspondence_mm':worst*1000,'native_body_px':201,'staff_estimated_length_px':139,'lower_shaft_scale':.75,'upper_shaft_scale':1.08,'triangles':len(target.data.polygons)},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/staff_final_geometry.blend'))
