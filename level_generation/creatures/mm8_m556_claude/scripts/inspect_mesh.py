"""Measure the selected Meshy return and preserve an isolated grounded authoring checkpoint."""
from pathlib import Path
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/body_geometry_v1/model_urls_glb.glb'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.join();mesh=bpy.context.object
mesh.parent=None;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
for o in list(bpy.data.objects):
 if o!=mesh:bpy.data.objects.remove(o,do_unlink=True)
mesh.name=mesh.data.name='Wasp'
co=np.array([v.co[:] for v in mesh.data.vertices]);zmin=float(co[:,2].min())
for v in mesh.data.vertices:v.co.z-=zmin
co[:,2]-=zmin
bm=bmesh.new();bm.from_mesh(mesh.data);bm.verts.ensure_lookup_table()
labels=np.full(len(co),-1,dtype=int);comps=[]
for v in bm.verts:
 if labels[v.index]>=0:continue
 k=len(comps);todo=[v];labels[v.index]=k;idx=[]
 while todo:
  x=todo.pop();idx.append(x.index)
  for e in x.link_edges:
   w=e.other_vert(x)
   if labels[w.index]<0:labels[w.index]=k;todo.append(w)
 comps.append(idx)
info=[]
for k,idx in enumerate(comps):
 q=co[idx];c=q.mean(0);_,s,vt=np.linalg.svd(q-c,full_matrices=False);t=(q-c)@vt[0]
 info.append(dict(id=k,n=len(idx),center=c.tolist(),lo=q.min(0).tolist(),hi=q.max(0).tolist(),axis_ends=[(c+vt[0]*t.min()).tolist(),(c+vt[0]*t.max()).tolist()]))
np.save(P/'work/components.npy',labels);np.save(P/'work/vertices.npy',co)
(P/'work/components.json').write_text(json.dumps(dict(bounds=[co.min(0).tolist(),co.max(0).tolist()],source_zmin=zmin,vertices=len(co),triangles=sum(len(f.vertices)-2 for f in mesh.data.polygons),components=info),indent=2))
assert np.all(labels>=0) and len(comps)>=1
for f in mesh.data.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_v1.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True
sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.57,.62,.67)
sc.render.resolution_x=1200;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
sc.render.film_transparent=True
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
c=Vector((co.min(0)+co.max(0))/2);extent=max(co.max(0)-co.min(0));cam.data.ortho_scale=extent*1.12
for name,d in [('front',(0,-1,0)),('side',(1,0,0)),('back',(0,1,0)),('top',(0,0,1)),('quarter',(1,-2,.25))]:
 direction=Vector(d).normalized();cam.location=c+direction*4*extent;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review'/('geometry_'+name+'.png'));bpy.ops.render.render(write_still=True)
print('ANATOMY',len(co),len(mesh.data.polygons),len(comps),co.min(0),co.max(0))
