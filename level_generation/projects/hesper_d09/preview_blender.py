"""Supplementary CPU geometry preview. This is not the required native game capture."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

project = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(project / 'source/hes_d09.blend'))
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 12
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 640, 400, 100
scene.render.image_settings.file_format = 'PNG'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 8
scene.view_settings.view_transform = 'Standard'
for obj in scene.objects:
    if obj.name.startswith(('PORTAL_', 'LIGHT_', 'DECOR_', 'SPAWN_')):
        obj.hide_render = True
for material in bpy.data.materials:
    if not material.use_nodes:
        continue
    bsdf = material.node_tree.nodes.get('Principled BSDF')
    image = next((n for n in material.node_tree.nodes if n.type == 'TEX_IMAGE'), None)
    if image and bsdf:
        bsdf.inputs['Roughness'].default_value = 0.85
        material.node_tree.links.new(image.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 0.15
md = json.loads((project / 'source/hes_d09.geometry.yml').read_text())
for light in md['lights']:
    marker = scene.objects[light['source_node']]
    data = bpy.data.lights.new(light['id'], 'POINT')
    data.color = tuple(v / 255 for v in light['color'])
    data.energy = (light['radius'] / 128) ** 2 * 12
    data.shadow_soft_size = 0.12
    obj = bpy.data.objects.new('PREVIEW_' + light['id'], data)
    scene.collection.objects.link(obj)
    obj.location = marker.matrix_world @ marker.data.vertices[0].co
cam = bpy.data.objects.new('PreviewCamera', bpy.data.cameras.new('PreviewCamera'))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.lens = 24
cam.data.clip_start, cam.data.clip_end = .05, 500
shots = json.loads((project / 'review/preview_shots.json').read_text())
output = project / 'review/blender01'
output.mkdir(exist_ok=True)
for index, shot in enumerate(shots, 1):
    cam.location = (Vector(shot['position']) + Vector((0, 0, 256))) / 128
    yaw, pitch = shot['yaw'], shot['pitch']
    direction = Vector((math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch)))
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(output / f'{index:02d}-{shot["name"]}.png')
    bpy.ops.render.render(write_still=True)

import os
os._exit(0)
