"""Measure the source mesh and render orthographic views for fitting the equine rig."""
from pathlib import Path
import json
import bpy
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/smart_topology_v1/model_urls_glb.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.join()
mesh=bpy.context.object
mesh.parent=None
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co) for v in mesh.data.vertices]);floor=float(co[:,2].min())
for v in mesh.data.vertices:v.co.z-=floor
co[:,2]-=floor
mesh.name=mesh.data.name='Unicorn'
for face in mesh.data.polygons:face.use_smooth=True
np.save(P/'work/source_vertices.npy',co)
print('BOUNDS',co.min(0),co.max(0),'vertices',len(co),'triangles',sum(len(f.vertices)-2 for f in mesh.data.polygons),flush=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.color_type='SINGLE'
sc.display.shading.single_color=(.67,.7,.74);sc.render.resolution_x=1200;sc.render.resolution_y=1000
sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
center=Vector((co.min(0)+co.max(0))/2);scale=max(co.max(0)-co.min(0))*1.3
for name,direction in [('front',(0,-1,0)),('side',(1,0,0)),('back',(0,1,0)),('top',(0,0,1)),('quarter',(1,-1,.25))]:
 cd=bpy.data.cameras.new(name);cd.type='ORTHO';cd.ortho_scale=scale
 cam=bpy.data.objects.new(name,cd);sc.collection.objects.link(cam);cam.location=center+Vector(direction)*4
 cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
 sc.render.filepath=str(P/f'review/source_{name}.png');bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(cam,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/source_grounded.blend'))
assert len(co)>100 and np.isfinite(co).all()
