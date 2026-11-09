"""Transfer returned UVs only after bijective triangle/corner correspondence at sub-millimetre tolerance."""
from pathlib import Path
import bpy,json
import numpy as np
from mathutils import Vector,kdtree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v5h.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();T=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);head=np.array([a.value for a in me.attributes['head'].data]);report={}
for part,layer in [('body','UVMap'),('head','HeadUV')]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p/f'meshy/texture_{part}_v1/model_urls_glb.glb'));objects=set(bpy.data.objects)-before;meshes=[o for o in objects if o.type=='MESH'];assert len(meshes)==1,len(meshes)
 src=meshes[0];sm=src.data;S=np.array([tuple(src.matrix_world@v.co) for v in sm.vertices]);polys=[f for f in me.polygons if part=='body' or head[f.index]]
 assert len(polys)==len(sm.polygons),(part,len(polys),len(sm.polygons))
 ids=sorted({i for f in polys for i in f.vertices});target=T[ids];scale=np.max(np.ptp(target,axis=0))/np.max(np.ptp(S,axis=0));S=S*scale+(target.max(0)+target.min(0))/2-(S.max(0)+S.min(0))*scale/2
 tree=kdtree.KDTree(len(sm.polygons))
 for f in sm.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();seen=set();worst=0;corner_worst=0
 if layer not in me.uv_layers:me.uv_layers.new(name=layer)
 uv=me.uv_layers[layer].data;su=sm.uv_layers.active.data
 for f in polys:
  _,index,d=tree.find(Vector(T[list(f.vertices)].mean(0)));assert index not in seen,(part,'duplicate face',index);seen.add(index);worst=max(worst,d);other=sm.polygons[index];assert len(f.vertices)==len(other.vertices)==3
  used=set()
  for li,vi in zip(f.loop_indices,f.vertices):
   distances=np.linalg.norm(S[list(other.vertices)]-T[vi],axis=1);k=int(np.argmin(distances));assert k not in used;used.add(k);corner_worst=max(corner_worst,float(distances[k]));uv[li].uv=su[other.loop_indices[k]].uv
 assert worst<.0002 and corner_worst<.0003,(part,worst,corner_worst)
 report[part]={'faces':len(polys),'unique_matches':len(seen),'max_centroid_mm':worst*1000,'max_corner_mm':corner_worst*1000,'scale':float(scale)}
 for o in objects:bpy.data.objects.remove(o,do_unlink=True)
 print('UV_VERIFIED',part,report[part])
me.uv_layers.active=me.uv_layers['UVMap'];(p/'work/uv_correspondence.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v6.blend'))
