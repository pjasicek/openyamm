"""Small independent Cycles lightmap validation; run with Blender --background --python."""
import json
import math
from pathlib import Path
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

out = Path(sys.argv[sys.argv.index('--') + 1])
out.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.max_bounces = 3
scene.cycles.diffuse_bounces = 2
scene.cycles.seed = 17
scene.render.threads_mode = 'FIXED'
scene.render.threads = 8
scene.world.use_nodes = True
world = scene.world.node_tree.nodes['Background']
world.inputs[0].default_value = (1, 1, 1, 1)
mat = bpy.data.materials.new('receiver')
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = (.7, .15, .08, 1)
bsdf.inputs['Roughness'].default_value = 1
image = bpy.data.images.new('lighting', width=128, height=128, float_buffer=True)
node = mat.node_tree.nodes.new('ShaderNodeTexImage')
node.image = image
mat.node_tree.nodes.active = node
mesh = bpy.data.meshes.new('floor')
mesh.from_pydata([(-4,-4,0),(4,-4,0),(4,4,0),(-4,4,0)], [], [(0,1,2,3)])
uv = mesh.uv_layers.new()
for item, coord in zip(uv.data, [(0,0),(1,0),(1,1),(0,1)]):
    item.uv = coord
floor = bpy.data.objects.new('floor', mesh)
scene.collection.objects.link(floor)
mesh.materials.append(mat)
bpy.ops.mesh.primitive_cube_add(location=(0,0,1), scale=(.6,.6,1))
wall = bpy.context.object
wall_mat = bpy.data.materials.new('green bounce wall')
wall_mat.use_nodes = True
wall_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.05,.65,.05,1)
wall.data.materials.append(wall_mat)
sun_data = bpy.data.lights.new('sun', 'SUN')
sun_data.energy = 1
sun_data.angle = math.radians(3)
sun = bpy.data.objects.new('sun', sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = Vector((1,-1,-1)).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.select_all(action='DESELECT')
floor.select_set(True)
bpy.context.view_layer.objects.active = floor
scene.render.bake.use_pass_color = False
scene.render.bake.use_pass_direct = True
scene.render.bake.use_pass_indirect = True
scene.render.bake.margin = 2
stats = {'blender': bpy.app.version_string, 'device': scene.cycles.device, 'samples': 32}
for name, sun_power, sky_power in [('sun', 1, 0), ('sky', 0, .25)]:
    sun_data.energy = sun_power
    world.inputs[1].default_value = sky_power
    t = time.monotonic()
    bpy.ops.object.bake(type='DIFFUSE')
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(128,128,4)
    np.save(out / (name + '.npy'), pixels)
    image.filepath_raw = str(out / (name + '.exr'))
    image.file_format = 'OPEN_EXR'
    image.save()
    stats[name] = {'seconds': time.monotonic()-t, 'min': pixels[:,:,:3].min(axis=(0,1)).tolist(),
                   'max': pixels[:,:,:3].max(axis=(0,1)).tolist(),
                   'lit_sample': pixels[15,15,:3].tolist(), 'shadow_sample': pixels[70,70,:3].tolist()}
sun_pixels = np.load(out / 'sun.npy')[:,:,:3]
sky_pixels = np.load(out / 'sky.npy')[:,:,:3]
assert np.isfinite(sun_pixels).all() and np.isfinite(sky_pixels).all()
assert np.ptp(sun_pixels[15,15]) < .01, 'Receiving red albedo was multiplied into irradiance'
assert np.max(sky_pixels[:,:,1] - sky_pixels[:,:,0]) > .01, 'Green diffuse bounce was lost'
assert np.max(sun_pixels) > .1 and np.min(sun_pixels) < .01, 'Sun/shadow separation missing'
stats['assertions'] = 'finite, receiver albedo excluded, colored bounce retained, sun shadow present'
(out / 'report.json').write_text(json.dumps(stats, indent=2)+'\n')
print(json.dumps(stats))
