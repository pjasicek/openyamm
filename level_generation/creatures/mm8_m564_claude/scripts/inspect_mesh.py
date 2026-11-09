"""Inspect the untouched Meshy mesh, measuring anatomy before local rigging."""
from pathlib import Path
import json
import bpy
import numpy as np
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / 'meshy/smart_topology_v2/model_urls_glb.glb'))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for obj in meshes:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.concatenate([np.array([tuple(v.co) for v in o.data.vertices]) for o in meshes])
np.save(P / 'work/source_vertices.npy', co)
lo, hi = co.min(0), co.max(0)
print('BOUNDS', lo, hi, 'DIMENSIONS', hi-lo, flush=True)
info = {'bounds': [lo.tolist(), hi.tolist()], 'objects': []}
for obj in meshes:
    obj.data.calc_loop_triangles()
    info['objects'].append({'name': obj.name, 'vertices': len(obj.data.vertices),
                            'triangles': len(obj.data.loop_triangles)})
print('MESHES', info['objects'], flush=True)
(P/'work/source_mesh.json').write_text(json.dumps(info, indent=2)+'\n')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.65, 0.68, 0.65)
sc.display.shading.show_cavity = True
sc.display.shading.show_shadows = False
sc.render.resolution_x = 1000
sc.render.resolution_y = 800
sc.render.resolution_percentage = 100
center = Vector((lo+hi)/2)
for name, direction in {'side': (1,0,0), 'front': (0,-1,0), 'top': (0,0,1),
                         'quarter': (1,-1,0.55)}.items():
    camera_data = bpy.data.cameras.new(name)
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = float(max(hi-lo)*1.5)
    camera = bpy.data.objects.new(name, camera_data)
    sc.collection.objects.link(camera)
    camera.location = center + Vector(direction)*4
    camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
    sc.camera = camera
    sc.render.filepath = str(P/'review'/('mesh_'+name+'.png'))
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/source_import.blend'))
