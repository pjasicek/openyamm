import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v3.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
me=o.data;T=np.array([v.co[:] for v in me.vertices]);report={}
for slot,label in [(1,'head')]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/f'{label}_retexture_v2/model_urls_glb.glb'));src=max((x for x in bpy.data.objects if x not in before and x.type=='MESH'),key=lambda x:len(x.data.polygons));sm=src.data;S=np.array([tuple(src.matrix_world@v.co) for v in sm.vertices]);ids=sorted({i for f in me.polygons if f.material_index==slot for i in f.vertices});sub=T[ids];scale=np.ptp(sub,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(sub.max(0)+sub.min(0))/2-(S.max(0)+S.min(0))/2*scale
 tree=kdtree.KDTree(len(sm.polygons))
 for f in sm.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();worst=0;corner=0;uerr=0;count=0
 for f in me.polygons:
  if f.material_index!=slot:continue
  hits=tree.find_n(Vector(T[list(f.vertices)].mean(0)),6);bestdist=hits[0][2];candidates=[q for q in hits if q[2]<bestdist+1e-7];_,j,d=max(candidates,key=lambda q:sm.polygons[q[1]].normal.dot(f.normal));worst=max(worst,d);sf=sm.polygons[j];assert len(sf.vertices)==len(f.vertices)==3
  for li,vi in zip(f.loop_indices,f.vertices):
   ds=np.linalg.norm(S[list(sf.vertices)]-T[vi],axis=1);k=int(ds.argmin());corner=max(corner,float(ds[k]));u=sm.uv_layers.active.data[sf.loop_indices[k]].uv;uerr=max(uerr,(me.uv_layers.active.data[li].uv-u).length);me.uv_layers.active.data[li].uv=u
  count+=1
 assert worst<1e-4 and corner<1e-4 ,(label,worst,corner,uerr)
 # Texture service welds sub-0.1 mm sliver corners; verified against the 0.35 m head.
 report[label]=dict(faces=count,centroid_error=worst,corner_error=corner,uv_change=uerr)
 for x in list(bpy.data.objects):
  if x not in before:bpy.data.objects.remove(x,do_unlink=True)
(P/'work/texture_uv_parity.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));print('UV_PARITY',report)
