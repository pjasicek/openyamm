"""Inspect the Smart Topology return, preserve all components and normalize the model."""
import bpy, bmesh, json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/smart_topology_v1/model_urls_glb.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.join(); obj=bpy.context.object; obj.name=obj.data.name='Body'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([v.co[:] for v in obj.data.vertices]); s=2.2/np.ptp(co[:,2]); obj.scale=(s,s,s)
bpy.ops.object.transform_apply(scale=True)
co=np.array([v.co[:] for v in obj.data.vertices]); upper=co[co[:,2]>co[:,2].min()+1.2]
obj.location=(-float((upper[:,0].min()+upper[:,0].max())/2),-float(np.median(upper[:,1])),-float(co[:,2].min()))
bpy.ops.object.transform_apply(location=True)
bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.to_mesh(obj.data);bm.free()
me=obj.data;co=np.array([v.co[:] for v in me.vertices]); edges=np.array([e.vertices[:] for e in me.edges]);adj=[[] for _ in co]
for a,b in edges:adj[a].append(int(b));adj[b].append(int(a))
seen=set();parts=[];part_ids=np.full(len(co),-1,dtype=int)
for i in range(len(co)):
 if i in seen:continue
 seen.add(i);todo=[i];ids=[]
 while todo:
  v=todo.pop();ids.append(v)
  for j in adj[v]:
   if j not in seen:seen.add(j);todo.append(j)
 idx=len(parts);part_ids[ids]=idx;c=co[ids]
 parts.append({'part':idx,'vertices':len(ids),'min':c.min(0).tolist(),'max':c.max(0).tolist(),'mean':c.mean(0).tolist()})
for face in me.polygons:face.use_smooth=True
me.materials.clear();mat=bpy.data.materials.new('MedusaClay');mat.diffuse_color=(.48,.53,.48,1);me.materials.append(mat)
attr=me.attributes.new('part','INT','POINT');attr.data.foreach_set('value',part_ids)
me.calc_loop_triangles();tri=np.array([t.vertices[:] for t in me.loop_triangles]);np.savez(P/'work/geometry.npz',co=co,edges=edges,tri=tri,parts=part_ids)
report={'vertices':len(co),'triangles':len(tri),'bbox':[co.min(0).tolist(),co.max(0).tolist()],'components':sorted(parts,key=lambda p:-p['vertices'])}
(P/'work/geometry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.studiolight_rotate_z=.3;sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.color_type='MATERIAL';sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('World');sc.world.color=(.13,.13,.15)
sc.render.resolution_x=sc.render.resolution_y=800;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,pos,target,scale in [('front',(0,-6,1.1),(0,0,1.1),2.4),('side',(6,0,1.1),(0,.1,1.1),2.4),('quarter',(4,-6,3),(0,.15,1.15),2.5),('back',(0,6,1.1),(0,0,1.1),2.4),('head',(2,-5,2.4),(0,0,1.93),.8),('hands',(0,-6,1.2),(0,0,1.2),1.5)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(P/'review'/f'geometry_{name}.png');bpy.ops.render.render(write_still=True)
