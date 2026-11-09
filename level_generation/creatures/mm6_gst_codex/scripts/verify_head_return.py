import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master_full.blend'));body=bpy.data.objects['Body'];me=body.data;faces=[f for f in me.polygons if f.material_index==1];T=np.array([body.matrix_world@v.co for v in me.vertices]);target=T[list({v for f in faces for v in f.vertices})];before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy/head_retexture_v2/model_urls_glb.glb'));src=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons));S=np.array([src.matrix_world@v.co for v in src.data.vertices]);scale=float(np.ptp(target,axis=0).max()/np.ptp(S,axis=0).max());S=S*scale+((target.max(0)+target.min(0))/2-(S.max(0)+S.min(0))/2*scale);tree=kdtree.KDTree(len(src.data.polygons))
for f in src.data.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
tree.balance();error=0.;uv_error=0.;matched=set()
for f in faces:
 _,i,d=tree.find(Vector(T[list(f.vertices)].mean(0)));error=max(error,d);sf=src.data.polygons[i];matched.add(i);assert len(sf.vertices)==len(f.vertices)
 for li,vi in zip(f.loop_indices,f.vertices):
  dist=np.linalg.norm(S[list(sf.vertices)]-T[vi],axis=1);k=int(np.argmin(dist));error=max(error,float(dist[k]));uv_error=max(uv_error,(me.uv_layers.active.data[li].uv-src.data.uv_layers.active.data[sf.loop_indices[k]].uv).length)
assert error<.001 and uv_error<.001 and len(matched)==len(faces),(error,uv_error,len(matched),len(faces))
(P/'work/head_v2_return_verified.json').write_text(json.dumps({'faces':len(faces),'max_surface_error_m':error,'max_uv_error':uv_error},indent=2));print('HEAD V2',len(faces),error,uv_error)
