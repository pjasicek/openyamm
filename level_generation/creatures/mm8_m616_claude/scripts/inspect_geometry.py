"""Inspect the preserved Meshy geometry; write only this project's work and review files."""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
V = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'v1'
R = P / 'review' / V
R.mkdir(exist_ok=True)
(P / 'work').mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / f'meshy/smart_topology_{V}/model_urls_glb.glb'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
assert meshes
report = []
for obj in meshes:
    co = np.array([tuple(obj.matrix_world @ v.co) for v in obj.data.vertices])
    obj.data.calc_loop_triangles()
    report.append(dict(name=obj.name, vertices=len(co), triangles=len(obj.data.loop_triangles),
                       minimum=co.min(0).tolist(), maximum=co.max(0).tolist()))
    for face in obj.data.polygons:
        face.use_smooth = True
co = np.concatenate([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in meshes])
assert np.isfinite(co).all()
np.save(P / f'work/raw_coordinates_{V}.npy', co)
(R / 'geometry_inventory.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.show_cavity = True
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.55, 0.65, 0.72)
scene.display.shading.background_type = 'WORLD'
scene.world = bpy.data.worlds.new('ReviewWorld')
scene.world.color = (0.07, 0.07, 0.07)
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
center = Vector((co.min(0) + co.max(0)) / 2)
extent = float(np.max(np.ptp(co, axis=0)))
cam = bpy.data.objects.new('ReviewCamera', bpy.data.cameras.new('ReviewCamera'))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.type = 'ORTHO'
cam.data.ortho_scale = extent * 1.12
for name, direction in [('front', (0, -1, 0)), ('back', (0, 1, 0)),
                        ('left', (1, 0, 0)), ('top', (0, 0, 1)), ('quarter', (1, -1.5, 0.6))]:
    cam.location = center + Vector(direction).normalized() * extent * 4
    cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(R / f'geometry_{name}.png')
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P / f'work/import_{V}.blend'))
