import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/flame_master.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
me=o.data;T=np.array([v.co[:] for v in me.vertices]);report={}
for slot,label in [(0,'body')]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/f'{label}_retexture_v1/model_urls_glb.glb'));src=max((x for x in bpy.data.objects if x not in before and x.type=='MESH'),key=lambda x:len(x.data.polygons));sm=src.data;S=np.array([tuple(src.matrix_world@v.co) for v in sm.vertices]);ids=sorted({i for f in me.polygons if f.material_index==slot for i in f.vertices});sub=T[ids];scale=np.ptp(sub,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(sub.max(0)+sub.min(0))/2-(S.max(0)+S.min(0))/2*scale
 tree=kdtree.KDTree(len(sm.polygons))
 for f in sm.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();surface=BVHTree.FromPolygons(S.tolist(),[list(f.vertices) for f in sm.polygons],all_triangles=True);texel_repairs=[];worst_surface=0;worst=0;uvmax=0;count=0;oral_count=0;repairs=[];omitted_slivers=[]
 orders=np.array([[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]])
 for f in me.polygons:
  if f.material_index!=slot:continue
  if me.attributes['oral'].data[f.index].value:
   oral_count+=1;continue # Oral caps receive a separate dark material, never the service paint.
  hits=tree.find_n(Vector(T[list(f.vertices)].mean(0)),12)
  faces=[sm.polygons[j] for _,j,_ in hits]
  verts=np.array([sf.vertices[:] for sf in faces]);old=np.array([me.uv_layers.active.data[i].uv[:] for i in f.loop_indices])
  coordinates=S[verts[:,orders]];errors=np.linalg.norm(coordinates-T[list(f.vertices)],axis=-1).max(-1)
  minimum=errors.min();candidates=np.argwhere(errors<minimum+1e-6);best=None
  for j,k in candidates:
   sf=faces[j];new=np.array([sm.uv_layers.active.data[sf.loop_indices[n]].uv[:] for n in orders[k]])
   change=float(np.linalg.norm(new-old,axis=1).max());candidate=(change,float(errors[j,k]),new)
   if best is None or candidate[0]<best[0]:best=candidate
  change,error,new=best;worst=max(worst,error);uvmax=max(uvmax,change);count+=1
  if error>=1e-4:
   # Retexture can retriangulate skinny faces; transfer sampled surface paint without changing the rig.
   distances=[surface.find_nearest(Vector(v))[3] for v in T[list(f.vertices)]]
   worst_surface=max(worst_surface,max(distances));assert max(distances)<1e-4,(f.index,distances)
   uv=old*2048;x0,y0=np.maximum(np.floor(uv.min(0)).astype(int)-1,0);x1,y1=np.minimum(np.ceil(uv.max(0)).astype(int)+1,2047)
   samples=0
   for py in range(y0,y1+1):
    for px in range(x0,x1+1):
     weights=np.linalg.solve(np.vstack([uv.T,np.ones(3)]),np.array([px+.5,py+.5,1]))
     if weights.min()<-.02:continue
     pos=weights@T[list(f.vertices)];point,normal,fi,distance=surface.find_nearest(Vector(pos))
     assert distance<1e-4,(f.index,distance)
     sf=sm.polygons[fi];tri=S[list(sf.vertices)];basis=np.column_stack([tri[0]-tri[2],tri[1]-tri[2]])
     ab=np.linalg.lstsq(basis,np.array(point)-tri[2],rcond=None)[0];w=np.array([ab[0],ab[1],1-ab.sum()])
     source=w@np.array([sm.uv_layers.active.data[li].uv[:] for li in sf.loop_indices])
     texel_repairs.append({'pixel':[px,2047-py],'source_uv':source.tolist()});samples+=1
   omitted_slivers.append({'face':f.index,'area_m2':f.area,'surface_distance_m':max(distances),'texels':samples})
   continue
  if change>1e-5:repairs.append({'face':f.index,'target_uv':old.tolist(),'source_uv':new.tolist()})
 # Keep the frozen non-overlapping rig UVs. Transfer paint for omitted coincident faces only.
 report[label]={'faces_verified':count,'oral_caps_painted_separately':oral_count,'corner_error':worst,'uv_change':uvmax,'repairs':repairs,'retriangulated_faces':omitted_slivers,'surface_error':worst_surface,'texel_repairs':texel_repairs}
 assert sum(x['area_m2'] for x in omitted_slivers)<3e-6
 print('UV_PARITY',label,{k:v for k,v in report[label].items() if k!='repairs'},'paint_transfers',len(repairs),flush=True)
 for x in list(bpy.data.objects):
  if x not in before:bpy.data.objects.remove(x,do_unlink=True)
(P/'work/texture_uv_parity.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));print('UV_PARITY complete')
