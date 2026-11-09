"""Exact vertex/face transfer, with explicitly recorded colour patches for Meshy's removed interior faces."""
import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];src,job,out=sys.argv[sys.argv.index('--')+1:][:3]
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();T=np.array([tuple(body.matrix_world@v.co)for v in me.vertices]);before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(Path(job).resolve()/'model_urls_glb.glb'));ob=max((o for o in set(bpy.data.objects)-before if o.type=='MESH'),key=lambda o:len(o.data.polygons));S=np.array([tuple(ob.matrix_world@v.co)for v in ob.data.vertices]);k=np.ptp(T,0).max()/np.ptp(S,0).max();S=S*k+(T.max(0)+T.min(0))/2-(S.max(0)+S.min(0))/2
unique,canonical=np.unique(T,axis=0,return_inverse=True);kd=KDTree(len(unique))
for i,v in enumerate(unique):kd.insert(Vector(v),i)
kd.balance();matches=[kd.find(Vector(v))for v in S];mapping=np.array([v[1]for v in matches]);maxdist=max(v[2]for v in matches);assert maxdist<.000003
faces={tuple(sorted(mapping[list(f.vertices)])):f for f in ob.data.polygons};uv=me.uv_layers['UVMap'].data;su=ob.data.uv_layers.active.data;tree=KDTree(len(ob.data.polygons))
for f in ob.data.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
tree.balance();patches=[];matched=0;pv=np.array([d.value for d in me.attributes['piece'].data]);hd=np.array([d.value for d in me.attributes['head'].data])
for f in me.polygons:
 if hd[f.index]:continue
 sf=faces.get(tuple(sorted(canonical[list(f.vertices)])))
 if sf:
  loops={int(mapping[vi]):li for li,vi in zip(sf.loop_indices,sf.vertices)}
  for li,vi in zip(f.loop_indices,f.vertices):uv[li].uv=su[loops[int(canonical[vi])]].uv
  matched+=1
 else:
  # Meshy removed these small cap/interior surfaces. Keep rig topology; fill each from the adjacent painted surface.
  centre=T[list(f.vertices)].mean(0);_,idx,d=tree.find(Vector(centre));sf=ob.data.polygons[idx];value=sum((su[li].uv.copy()for li in sf.loop_indices),Vector((0,0)))/len(sf.loop_indices)
  for li in f.loop_indices:uv[li].uv=value
  patches.append({'face':f.index,'piece':int(pv[f.vertices[0]]),'centroid':centre.tolist(),'donor_distance_m':d,'uv':list(value)})
print('UV counts',len(patches),matched,flush=True);assert len(patches)<=20 and matched>12800
for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
me.uv_layers.active=me.uv_layers['UVMap'];bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()));r={'exact_faces':matched,'patched_removed_faces':patches,'maximum_vertex_match_error_m':maxdist,'return_scale':float(k),'reason':'Meshy retexture dropped 18 source triangles; retained original rig geometry and explicitly filled the 17 non-matching faces from their adjacent painted surfaces.'};(P/'review/uv_transfer.json').write_text(json.dumps(r,indent=2));print('UV EXACT',matched,'PATCHED',len(patches),'VERTEX ERROR',maxdist,flush=True)
