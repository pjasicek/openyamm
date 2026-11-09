"""Normalize the Meshy wolf and measure its anatomy before placing a skeleton."""
import bpy
import json
import math
from pathlib import Path
import numpy as np
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(PROJECT / 'meshy/smart_topology_v1/model_urls_glb.glb'))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
mesh = bpy.context.object
mesh.name = mesh.data.name = 'Wolf'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([v.co[:] for v in mesh.data.vertices])
print('ORIGINAL BOUNDS', co.min(0), co.max(0), flush=True)
mesh.location.z -= co[:, 2].min()
bpy.ops.object.transform_apply(location=True)
co = np.array([v.co[:] for v in mesh.data.vertices])
for face in mesh.data.polygons:
    face.use_smooth = True
mesh.data.calc_loop_triangles()
report = {'bounds': [co.min(0).tolist(), co.max(0).tolist()],
          'vertices': len(co), 'triangles': len(mesh.data.loop_triangles)}
np.save(PROJECT / 'work/mesh_vertices.npy', co)
(PROJECT / 'work/geometry_report.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT / 'work/mesh_v1.blend'))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.show_cavity = True
sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (.62, .63, .65)
sc.display.shading.background_type = 'WORLD'
sc.world = bpy.data.worlds.new('ReviewWorld')
sc.world.color = (.12, .12, .12)
sc.render.resolution_x = 1200
sc.render.resolution_y = 800
sc.render.resolution_percentage = 100
center = Vector((co.min(0) + co.max(0)) / 2)
extent = float(np.max(np.ptp(co, axis=0)))
cam = bpy.data.objects.new('ReviewCamera', bpy.data.cameras.new('ReviewCamera'))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = 'ORTHO'
cam.data.ortho_scale = extent * 1.15
for name, direction in [('side', (1, 0, 0)), ('front', (0, -1, 0)),
                        ('top', (0, 0, 1)), ('quarter', (1, -1, .5))]:
    cam.location = center + Vector(direction).normalized() * extent * 3
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = str(PROJECT / f'review/mesh_{name}.png')
    bpy.ops.render.render(write_still=True)
print('GEOMETRY', json.dumps(report), flush=True)
