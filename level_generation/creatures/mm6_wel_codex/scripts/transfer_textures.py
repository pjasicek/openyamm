"""Require one-to-one unchanged triangles; transfer only body UVs and verify head UV preservation."""
import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));rig=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();T=np.array([o.matrix_world@v.co for v in me.vertices]);reports={}
for label,slot in [('body',0),('head',1)]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/f'meshy/{label}_retexture_v1/model_urls_glb.glb'));src=max((x for x in bpy.data.objects if x not in before and x.type=='MESH'),key=lambda x:len(x.data.polygons));S=np.array([src.matrix_world@v.co for v in src.data.vertices]);polys=[p for p in me.polygons if p.material_index==slot];target=T if label=='body' else T[list({v for f in polys for v in f.vertices})];scale=np.ptp(target,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+((target.max(0)+target.min(0))/2-(S.max(0)+S.min(0))/2*scale);tree=kdtree.KDTree(len(src.data.polygons))
 for f in src.data.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();worst=0.;corners=0.;uverr=0.;matched=set()
 for f in polys:
  _,i,dist=tree.find(Vector(T[list(f.vertices)].mean(0)));sf=src.data.polygons[i];assert len(sf.vertices)==len(f.vertices);worst=max(worst,dist);matched.add(i)
  for li,vi in zip(f.loop_indices,f.vertices):
   dd=np.linalg.norm(S[list(sf.vertices)]-T[vi],axis=1);j=int(np.argmin(dd));corners=max(corners,float(dd[j]));uv=src.data.uv_layers.active.data[sf.loop_indices[j]].uv
   if slot==0:me.uv_layers.active.data[li].uv=uv
   else:uverr=max(uverr,(me.uv_layers.active.data[li].uv-uv).length)
 assert worst<.0005 and corners<.0005 and len(matched)==len(polys),(label,worst,corners,len(matched),len(polys))
 if slot==1:assert uverr<.0001,(label,uverr)
 reports[label]={'faces':len(polys),'unique_matches':len(matched),'max_centroid_error_m':worst,'max_corner_error_m':corners,'head_uv_error':uverr,'normalization_scale':float(scale)}
 for ob in list(bpy.data.objects):
  if ob not in before:bpy.data.objects.remove(ob,do_unlink=True)
# Remove the redundant head allocation and balance tail versus fingers without rotating charts.
source_uv=np.array([v.uv[:] for v in me.uv_layers.active.data]);np.save(P/'work/body_source_uv.npy',source_uv);uv=me.uv_layers.active.data;part=me.attributes['part'].data
for f in me.polygons:
 if f.material_index:continue
 pn=part[f.vertices[0]].value;factor=2.0 if pn==5 else .55 if pn in [1,6] else 1.10 if pn==0 else 1
 for li in f.loop_indices:uv[li].uv*=factor
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(me)
for f in bm.faces:f.select_set(f.material_index==0)
bmesh.update_edit_mesh(me);bpy.ops.uv.pack_islands(margin=.003,rotate=False,scale=True,shape_method='CONCAVE');bpy.ops.object.mode_set(mode='OBJECT')
reports['body']['repacked_without_rotation']=True;reports['body']['relative_chart_scale']={'tail':2.,'hands':.55,'torso':1.10,'others':1.}
(P/'work/uv_transfer.json').write_text(json.dumps(reports,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));print(reports)

import runpy
for script in ["uv_raster.py","returned_uv_gate.py"]:runpy.run_path(str(P/"scripts"/script),run_name="__main__")
