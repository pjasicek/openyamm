"""Inspect the paid single-fish geometry before rigging or texturing."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
import numpy as np

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/fish_geometry_v1/model_urls_glb.glb'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
fish = bpy.context.object
fish.name = 'Fish'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([v.co[:] for v in fish.data.vertices])
lo, hi = co.min(0), co.max(0)
print('FISH_RAW', len(co), sum(len(f.vertices)-2 for f in fish.data.polygons), lo.tolist(), hi.tolist(), flush=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.render.resolution_x = 1000
sc.render.resolution_y = 750
sc.render.resolution_percentage = 100
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (.5,.6,.7)
sc.display.shading.show_cavity = True
sc.display.shading.show_shadows = True
center = Vector((lo+hi)/2)
camera = bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'))
sc.collection.objects.link(camera)
sc.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = float(max(hi-lo)*1.3)
for name, direction in [('side',(1,0,0)),('front',(0,-1,0)),('top',(0,0,1)),('quarter',(1,-1,.5))]:
    camera.location = center + Vector(direction).normalized()*5
    camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath = str(P/f'review/geometry_{name}.png')
    bpy.ops.render.render(write_still=True)
camera.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fish_import.blend'))
(P/'work/fish_geometry.json').write_text(json.dumps({'vertices':len(co),'triangles':sum(len(f.vertices)-2 for f in fish.data.polygons),'bounds':[lo.tolist(),hi.tolist()]},indent=2)+'\n')
