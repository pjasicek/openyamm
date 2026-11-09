import bpy, json, sys, math
from pathlib import Path
import numpy as np
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
for d in ['work','review/geometry','texturing','export','textures']:
    (P/d).mkdir(exist_ok=True,parents=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/smart_topology_v1/model_urls_glb.glb'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.join()
m=bpy.context.object
m.parent=None
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
m.name=m.data.name='Juggernaut'
co=np.array([tuple(v.co) for v in m.data.vertices]);lo=co.min(0);hi=co.max(0)
print('ORIGINAL_BOUNDS',lo.tolist(),hi.tolist(),flush=True)
m.location.z=-lo[2]
bpy.ops.object.transform_apply(location=True)
co=np.array([tuple(v.co) for v in m.data.vertices]);np.save(P/'work/geometry_vertices.npy',co)
for o in list(bpy.data.objects):
    if o!=m:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_v1.blend'))
info={'vertices':len(m.data.vertices),'triangles':sum(len(f.vertices)-2 for f in m.data.polygons),'bounds':[co.min(0).tolist(),co.max(0).tolist()]}
(P/'work/geometry_info.json').write_text(json.dumps(info,indent=2))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(0.64,0.55,0.6)
sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(0.12,0.12,0.12)
sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
c=Vector((co.min(0)+co.max(0))/2);ext=float((co.max(0)-co.min(0)).max())
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=ext*1.15
for name,d in [('front',(0,-1,.02)),('side',(1,0,.02)),('back',(0,1,.02)),('quarter',(1,-1,.3))]:
    cam.location=c+Vector(d).normalized()*4*ext;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(P/'review/geometry'/f'{name}.png');bpy.ops.render.render(write_still=True)
print('GEOMETRY',json.dumps(info),flush=True)
