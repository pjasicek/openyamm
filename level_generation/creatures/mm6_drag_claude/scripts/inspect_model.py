import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/smart_topology_v1/model_urls_glb.glb'))
obs=[o for o in bpy.data.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in obs:o.select_set(True)
bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=obs[0];o.name='Body';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([v.co[:] for v in o.data.vertices]);print('BOUNDS',co.min(0),co.max(0))
o.location.z=-co[:,2].min();bpy.ops.object.transform_apply(location=True);co=np.array([v.co[:] for v in o.data.vertices])
for f in o.data.polygons:f.use_smooth=True
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();seen=set();parts=[]
for v in bm.verts:
 if v.index in seen:continue
 todo=[v];ids=[];seen.add(v.index)
 while todo:
  q=todo.pop();ids.append(q.index)
  for e in q.link_edges:
   w=e.other_vert(q)
   if w.index not in seen:seen.add(w.index);todo.append(w)
 parts.append(ids)
bm.free();parts.sort(key=len,reverse=True);attr=o.data.attributes.new('part','INT','POINT');report=[]
for j,ids in enumerate(parts):
 for i in ids:attr.data[i].value=j
 a=co[ids];report.append(dict(part=j,verts=len(ids),min=a.min(0).tolist(),max=a.max(0).tolist(),center=a.mean(0).tolist()))
(P/'work/components.json').write_text(json.dumps(report,indent=2));np.save(P/'work/rest_co.npy',co)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/static_v1.blend'));print('COMPONENTS',json.dumps(report))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.62,.66,.64);sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False;sc.render.resolution_x=1100;sc.render.resolution_y=800;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';target=Vector((0,float((co[:,1].min()+co[:,1].max())/2),float(co[:,2].max()/2)))
for name,d in [('front',(0,-6,0)),('side',(6,0,0)),('back',(0,6,0)),('top',(0,0,6)),('three_quarter',(4,-6,2))]:
 cam.location=target+Vector(d);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=max(np.ptp(co,axis=0))*1.65;sc.render.filepath=str(P/'review'/f'clay_{name}.png');bpy.ops.render.render(write_still=True)
