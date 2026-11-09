"""Verify Meshy changed textures only, preserving the prepared geometry and UV corners."""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];W=P/'work/parts_v5'
bpy.ops.wm.open_mainfile(filepath=str(W/'parts.blend'))
report={}
for part in ['body','wings']:
 target=bpy.data.objects[part.title()];before=set(bpy.data.objects)
 bpy.ops.import_scene.gltf(filepath=str(P/f'meshy/{part}_texture_v5/model_urls_glb.glb'))
 new=set(bpy.data.objects)-before;sources=[o for o in new if o.type=='MESH'];assert len(sources)==1
 source=sources[0];S=np.array([source.matrix_world@v.co for v in source.data.vertices]);T=np.array([v.co[:] for v in target.data.vertices])
 scale=np.ptp(T,axis=0).max()/np.ptp(S,axis=0).max();offset=(T.max(0)+T.min(0)-scale*(S.max(0)+S.min(0)))/2;S=S*scale+offset
 assert len(source.data.polygons)==len(target.data.polygons)
 tree=kdtree.KDTree(len(source.data.polygons))
 for poly in source.data.polygons:tree.insert(Vector(S[list(poly.vertices)].mean(0)),poly.index)
 tree.balance();used=set();maxgeometry=0;maxuv=0;uv=target.data.uv_layers.active.data;srcuv=source.data.uv_layers.active.data
 for poly in target.data.polygons:
  _,i,_=tree.find(Vector(T[list(poly.vertices)].mean(0)));assert i not in used;used.add(i);sp=source.data.polygons[i]
  for li in poly.loop_indices:
   point=T[target.data.loops[li].vertex_index];sl=min(sp.loop_indices,key=lambda k:np.linalg.norm(S[source.data.loops[k].vertex_index]-point))
   maxgeometry=max(maxgeometry,float(np.linalg.norm(S[source.data.loops[sl].vertex_index]-point)))
   maxuv=max(maxuv,(uv[li].uv-srcuv[sl].uv).length)
 assert maxgeometry<.0002,(part,maxgeometry)
 assert maxuv<.0001,(part,maxuv)
 report[part]={'triangles':len(used),'max_geometry_error_m':maxgeometry,'max_uv_error':maxuv,'source_geometry_used':False}
 for obj in new:bpy.data.objects.remove(obj,do_unlink=True)
(W/'texture_correspondence.json').write_text(json.dumps(report,indent=2));print('VERIFIED_TEXTURE_PARTS',report)
