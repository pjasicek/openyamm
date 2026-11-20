"""Blender MCP view of the written native fixture, with ceilings hidden for review."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path('/home/pjasicek/github/OpenYAMM')
PROJECT = ROOT / 'level_generation/projects/brackenford_greywatch'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file

data = parse_blv_file(PROJECT / 'calibration/calibration.blv')['payload']
scene = bpy.data.scenes.new('Native calibration cutaway')
bpy.context.window.scene = scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 12
scene.render.resolution_x = 960
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new('Calibration inspection world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.22,.25,.3,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .7
metadata = json.loads((PROJECT / 'calibration/calibration.geometry.yml').read_text())
materials = {v['texture']: (bpy.data.materials[v['source_material']], v['texture_width'], v['texture_height'])
             for v in metadata['materials']}
vertices, faces, uvs, keys = [], [], [], []
for face in data['faces']:
    if face['is_portal'] or face['facet_type'] in (5, 6):
        continue
    material, width, height = materials[face['texture_name']]
    offset = len(vertices)
    vertices.extend(tuple(data['vertices'][i][a] / 128 for a in 'xyz') for i in face['vertex_indices'])
    faces.append(tuple(range(offset, len(vertices))))
    uvs.extend((u / width, 1 - v / height) for u, v in zip(face['texture_us'], face['texture_vs']))
    keys.append(face['texture_name'])
mesh = bpy.data.meshes.new('Native calibration')
mesh.from_pydata(vertices, [], faces)
mesh.update()
obj = bpy.data.objects.new('Native BLV floors and walls', mesh)
scene.collection.objects.link(obj)
for material, width, height in materials.values():
    mesh.materials.append(material)
for polygon, key in zip(mesh.polygons, keys):
    polygon.material_index = list(materials).index(key)
layer = mesh.uv_layers.new()
for loop, uv in zip(layer.data, uvs):
    loop.uv = uv
camera_data = bpy.data.cameras.new('Native fixture camera')
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 30
camera = bpy.data.objects.new('Native fixture camera', camera_data)
scene.collection.objects.link(camera)
camera.location = (22, 24, 28)
camera.rotation_euler = (Vector((8,4,3)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera
sun_data = bpy.data.lights.new('Inspection sun', 'SUN')
sun_data.energy = 2
sun = bpy.data.objects.new('Inspection sun', sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (.3,-.4,-.5)
scene.render.filepath = str(PROJECT / 'calibration/native_cutaway.png')
bpy.ops.render.render(write_still=True)
print(scene.render.filepath)
