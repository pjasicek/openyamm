"""Verify unchanged surfaces and transfer only the returned UVs to the retained animated master."""
import bpy,bmesh,json,sys,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;r.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(P/'work/anim_v1.blend'),link=False) as (source,target):target.actions=source.actions
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();T=np.array([o.matrix_world@v.co for v in me.vertices]);report={}
for label,slot in [('body',0),('head',1)]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/f'meshy/{label}_retexture_v1/model_urls_glb.glb'));src=max((ob for ob in bpy.data.objects if ob not in before and ob.type=='MESH'),key=lambda ob:len(ob.data.polygons));S=np.array([src.matrix_world@v.co for v in src.data.vertices]);polys=[f for f in me.polygons if f.material_index==slot];target=T if label=='body' else T[list({v for f in polys for v in f.vertices})];scale=np.ptp(target,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+((target.max(0)+target.min(0))/2-(S.max(0)+S.min(0))/2*scale)
 tree=kdtree.KDTree(len(src.data.polygons))
 for f in src.data.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();worst=0.;uv_error=0.;corner=0.;matched=set();patches=[]
 for f in polys:
  _,i,d=tree.find(Vector(T[list(f.vertices)].mean(0)));sf=src.data.polygons[i];assert len(sf.vertices)==len(f.vertices)
  if d>.001:
   assert label=='body' and f.index==10017 and d<.010,'Unexpected changed topology'
   uv_source=np.array([src.data.uv_layers.active.data[li].uv[:] for li in sf.loop_indices]);co=S[list(sf.vertices)];source_uv=[]
   for vi in f.vertices:
    w=np.linalg.lstsq(np.column_stack([co[1]-co[0],co[2]-co[0]]),T[vi]-co[0],rcond=None)[0];weights=np.maximum([1-w.sum(),*w],0);weights/=weights.sum();source_uv.append((weights@uv_source).tolist())
   target_uv=[(.965,.04),(.990,.04),(.978,.063)]
   for li,uv in zip(f.loop_indices,target_uv):me.uv_layers.active.data[li].uv=uv
   patches.append({'face':f.index,'region':'right shoulder rear, pale cloth','source':source_uv,'target':target_uv,'source_distance_m':d});continue
  worst=max(worst,d);matched.add(i)
  for li,vi in zip(f.loop_indices,f.vertices):
   dist=np.linalg.norm(S[list(sf.vertices)]-T[vi],axis=1);k=int(np.argmin(dist));corner=max(corner,float(dist[k]));uv=src.data.uv_layers.active.data[sf.loop_indices[k]].uv
   if slot==1:uv_error=max(uv_error,(me.uv_layers.active.data[li].uv-uv).length)
   else:me.uv_layers.active.data[li].uv=(uv.x*.96,uv.y)
 assert worst<.001 and corner<.001 and len(matched)+len(patches)==len(polys),(label,worst,corner,len(matched),len(polys))
 if slot==1:assert uv_error<.001,(label,uv_error)
 report[label]={'faces':len(polys),'unique_correspondences':len(matched),'centroid_error_m':worst,'corner_error_m':corner,'original_uv_error':uv_error,'normalization_scale':float(scale),'patches':patches}
 for ob in list(bpy.data.objects):
  if ob not in before:bpy.data.objects.remove(ob,do_unlink=True)
# The full-body retexture spends atlas space on the separately textured hood. Repack body charts without rotation.
source_uv=np.array([v.uv[:] for v in me.uv_layers.active.data]);source_uv[:,0]/=.96
for patch in report['body']['patches']:
 for li,uv in zip(me.polygons[patch['face']].loop_indices,patch['source']):source_uv[li]=uv
np.save(P/'work/body_source_uv.npy',source_uv)
for ob in bpy.context.scene.objects:ob.select_set(ob==o)
bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(me)
for f in bm.faces:f.select_set(f.material_index==0)
bmesh.update_edit_mesh(me);bpy.ops.uv.pack_islands(margin=.004,rotate=False,scale=True);bpy.ops.object.mode_set(mode='OBJECT')
report['body']['repacked_without_rotation']=True
(P/'work/uv_transfer.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));print(report)
for name in ['uv_raster.py','uv_gate.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
