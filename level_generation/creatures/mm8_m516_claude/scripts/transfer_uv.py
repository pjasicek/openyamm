"""Transfer each texture job's UVs onto our unchanged, animated mesh using exact triangle correspondence."""
import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree,geometry
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='FIXED',ngon_method='EAR_CLIP');bm.to_mesh(me);bm.free()
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();T=np.array([v.co[:] for v in me.vertices]);reports={}
for slot,job in [(0,'body_retexture_v1'),(1,'head_retexture_v1')]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/job/'model_urls_glb.glb'));src=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons));S=np.array([src.matrix_world@v.co for v in src.data.vertices]);polys=[f for f in me.polygons if slot==0 or f.material_index==slot];ids=np.unique([v for f in polys for v in f.vertices]);target=T if slot==0 else T[ids];scale=np.ptp(target,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(target.max(0)+target.min(0))*.5-(S.max(0)+S.min(0))*.5*scale
 tree=kdtree.KDTree(len(src.data.polygons))
 for f in src.data.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();surface=BVHTree.FromPolygons([Vector(v) for v in S],[list(f.vertices) for f in src.data.polygons],all_triangles=True);caps=[];head_projection=[];projection_error=0.;head_error=0.
 suv=src.data.uv_layers.active.data;tuv=me.uv_layers.active.data;worst=corner=0.
 for f in polys:
  _,idx,dist=tree.find(Vector(T[list(f.vertices)].mean(0)));sf=src.data.polygons[idx];sc=S[list(sf.vertices)]
  errors=np.min(np.linalg.norm(T[list(f.vertices)][:,None]-sc[None],axis=2),axis=1)
  if dist>.0001 or errors.max()>.0001:
   raise AssertionError((job,f.index,dist,float(errors.max()),T[list(f.vertices)].tolist()))
  else:
   worst=max(worst,dist);corner=max(corner,float(errors.max()))
   for li,vi in zip(f.loop_indices,f.vertices):
    k=int(np.argmin(np.linalg.norm(sc-T[vi],axis=1)));tuv[li].uv=suv[sf.loop_indices[k]].uv
 assert max(worst,corner)<.0001 and len(caps)<=10 and projection_error<.008 and head_error<.0001,(job,worst,corner,caps,projection_error)
 reports[job]={'faces':len(polys),'max_centroid_error':worst,'max_corner_error':corner,'retessellated_hand_cap_faces':caps,'cap_projection_error':projection_error,'head_paint_projection_faces':len(head_projection),'head_paint_projection_error':head_error}
 if slot==0:
  saved=me.uv_layers.get('BodyRetextureUV') or me.uv_layers.new(name='BodyRetextureUV')
  for dst,source in zip(saved.data,tuv):dst.uv=source.uv.copy()
 me.uv_layers.active=me.uv_layers['UVMap']
 for o in list(bpy.data.objects):
  if o not in before:bpy.data.objects.remove(o,do_unlink=True)
(P/'work/uv_transfer.json').write_text(json.dumps(reports,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));print(reports)
