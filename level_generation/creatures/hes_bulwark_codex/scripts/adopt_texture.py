"""Compare every returned triangle/corner; carry its UVs onto the approved rig without moving vertices."""
import json,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/bulwark_uv.blend'))
body=bpy.data.objects['Bulwark']; rig=bpy.data.objects['BulwarkRig']
bpy.context.scene.frame_set(0)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/bulwark_retexture_v1/model_urls_glb.glb'))
added=[o for o in bpy.data.objects if o not in before]; meshes=[o for o in added if o.type=='MESH'];assert len(meshes)==1
ret=meshes[0];ret.data.transform(ret.matrix_world);ret.matrix_world=Matrix();ret.parent=None
co=np.array([v.co[:] for v in body.data.vertices]);rc=np.array([v.co[:] for v in ret.data.vertices])
scale=np.ptp(co,axis=0)/np.ptp(rc,axis=0);assert np.ptp(scale)<1e-5
s=float(scale.mean());shift=(co.min(0)+co.max(0))/2-s*(rc.min(0)+rc.max(0))/2
ret.data.transform(Matrix.Translation(Vector(shift))@Matrix.Scale(s,4))
ret.data.update();body.data.update()
assert len(body.data.polygons)==len(ret.data.polygons)==10632
kd=KDTree(len(ret.data.polygons))
for f in ret.data.polygons:kd.insert(f.center,f.index)
kd.balance();seen=set();deltas=[];errors=[]
uv=body.data.uv_layers.active.data;ruv=ret.data.uv_layers.active.data
for f in body.data.polygons:
 _,idx,dist=kd.find(f.center);assert idx not in seen and dist<2e-6,(idx,dist);seen.add(idx)
 rf=ret.data.polygons[idx];assert len(f.vertices)==len(rf.vertices)==3
 matched=[]
 for loop in f.loop_indices:
  pos=body.data.vertices[body.data.loops[loop].vertex_index].co
  rloop=min(rf.loop_indices,key=lambda l:(ret.data.vertices[ret.data.loops[l].vertex_index].co-pos).length)
  error=(ret.data.vertices[ret.data.loops[rloop].vertex_index].co-pos).length;assert error<2e-6
  matched.append(rloop);errors.append(error);deltas.append((uv[loop].uv-ruv[rloop].uv).length)
  uv[loop].uv=ruv[rloop].uv
 assert len(set(matched))==3
tri=np.array([[body.data.vertices[v].co[:] for v in f.vertices] for f in body.data.polygons])
uvs=np.array([[uv[l].uv[:] for l in f.loop_indices] for f in body.data.polygons])
part=np.array([x.value for x in body.data.attributes['part'].data])
np.savez(P/'work/bulwark_tex_tris.npz',co=tri,uv=uvs,n=np.array([f.normal[:] for f in body.data.polygons]),part=part)
body.data.materials.clear();material=ret.data.materials[0];material.name='Bulwark';body.data.materials.append(material)
for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/bulwark_textured_rig.blend'))
d=np.array(deltas);report={'triangles':len(seen),'returned_scale':s,'returned_translation':shift.tolist(),'max_corner_position_error_m':max(errors),'max_uv_delta':float(d.max()),'max_uv_delta_texels_2k':float(d.max()*2048),'moved_corners_gt_half_texel':int((d>0.5/2048).sum()),'corners':len(d),'decision':'Keep approved geometry and rig; adopt returned UVs by bijective exact triangle/corner match','return_sha256':hashlib.sha256((P/'meshy/bulwark_retexture_v1/model_urls_glb.glb').read_bytes()).hexdigest()}
(P/'review/geometry/retexture_compare.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
