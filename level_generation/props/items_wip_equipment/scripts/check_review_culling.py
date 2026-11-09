"""Verify that the equipment review renderer hides a single plane's back face."""
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector

project = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project / 'scripts'))
from review_items import set_culling
folder = project / 'work/culling_selfcheck'
folder.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_plane_add(size=2)
material = bpy.data.materials.new('single_sided')
material.use_nodes = True
set_culling(material)
bpy.context.object.data.materials.append(material)
camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
bpy.context.scene.collection.objects.link(camera)
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 3
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 1
scene.render.resolution_x = scene.render.resolution_y = 32
scene.render.film_transparent = True
results = {}
for side, height in [('front', 3), ('back', -3)]:
    camera.location = (0, 0, height)
    camera.rotation_euler = (-Vector(camera.location)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(folder / f'{side}.png')
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(scene.render.filepath, check_existing=False)
    pixels = np.asarray(image.pixels[:]).reshape(32, 32, 4)
    results[side] = float(pixels[12:20, 12:20, 3].mean())
(project / 'review/culling_selfcheck.json').write_text(json.dumps(results, indent=2) + '\n')
print('CULLING_SELF_CHECK', results, flush=True)
assert results['front'] > 0.99 and results['back'] < 0.01, results
