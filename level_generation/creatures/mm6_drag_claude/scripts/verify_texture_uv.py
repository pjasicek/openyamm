import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));o=bpy.data.objects['Body'];me=o.data;T=np.array([v.co[:] for v in me.vertices]);report={}
for slot,label in enumerate(['body','head']):
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'work'/f'{label}_upload.glb'));up=next(x for x in bpy.data.objects if x not in before and x.type=='MESH');U=np.array([up.matrix_world@v.co for v in up.data.vertices]);bpy.data.objects.remove(up,do_unlink=True)
 bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/f'{label}_texture_v2/model_urls_glb.glb'));src=next(x for x in bpy.data.objects if x not in before and x.type=='MESH');sm=src.data;S=np.array([src.matrix_world@v.co for v in sm.vertices]);scale=np.ptp(U,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(U.max(0)+U.min(0))/2-(S.max(0)+S.min(0))/2*scale
 # The service removes degenerate triangles, but preserves corner UVs. Match corners by both position and UV.
 tree=kdtree.KDTree(len(sm.loops));uv=sm.uv_layers.active.data
 for li,loop in enumerate(sm.loops):tree.insert(Vector(S[loop.vertex_index]),li)
 tree.balance();worst=0;uerr=0;unmatched=[];count=0;changed=[]
 me.calc_loop_triangles()
 for f in me.loop_triangles:
  if f.material_index!=slot:continue
  for li,vi in zip(f.loops,f.vertices):
   old=me.uv_layers.active.data[li].uv;hits=tree.find_n(Vector(T[vi]),32);near=tree.find_range(Vector(T[vi]),1e-4)
   if not near:unmatched.append({'vertex':vi,'distance':hits[0][2]});continue
   _,j,d=min(near,key=lambda q:(uv[q[1]].uv-old).length);delta=(uv[j].uv-old).length;worst=max(worst,d);
   if f.area>1e-7:
    uerr=max(uerr,delta)
    if delta>1e-4:changed.append({"area":f.area,"position_error":d,"uv_error":delta})
   count+=1
 # Existing UVs are deliberately retained: fresh UVs would invalidate degenerate corners omitted by Meshy.
 report[label]={'matched_corners':count,'unmatched_corners':len(unmatched),'max_position_error':worst,'max_uv_error':uerr,'unmatched':unmatched[:15],'changed_corners':changed}
 # Meshy drops degenerate/small seam faces. Retain their original UVs; never substitute an unrelated island.
 assert len(changed)<20 and len(changed)/count<.002,(label,report[label]);assert not unmatched,(label,report[label])
 for x in list(bpy.data.objects):
  if x not in before:bpy.data.objects.remove(x,do_unlink=True)
(P/'work/texture_uv_parity.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));print('UV_PARITY',report)
