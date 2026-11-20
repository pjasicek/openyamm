"""Run in Blender with REPO set. Creates an independent scene; keeps existing work."""
import json
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

root = Path(REPO)
out = root / 'level_generation/ui/hud_inventory/minimap_study_20260927/new_sorpigal'
data = json.loads((out / 'scene_data.json').read_text())
scene = bpy.data.scenes.new('New Sorpigal minimap comparison')
bpy.context.window.scene = scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 2048
scene.render.resolution_y = 2048
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.view_settings.view_transform = 'Standard'
scene.world = bpy.data.worlds.new('Minimap soft daylight')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.75, .8, 1, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65


def material(name, path):
    mat = bpy.data.materials.new('Minimap ' + name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = 1
    bsdf.inputs['Specular IOR Level'].default_value = 0
    texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(str(path), check_existing=True)
    texture.interpolation = 'Linear'
    mat.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    return mat


def mesh_object(name, vertices, faces, uvs, materials, indices):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    for mat in materials:
        mesh.materials.append(mat)
    for polygon, index in zip(mesh.polygons, indices):
        polygon.material_index = index
    layer = mesh.uv_layers.new(name='Map UV')
    for loop, uv in zip(layer.data, uvs):
        loop.uv = uv
    return obj


terrain_material = material('terrain', out / 'materials/terrain.png')
vertices = [((x-64)*4, (64-y)*4, data['height_map'][y*128+x]/4) for y in range(128) for x in range(128)]
faces = []
for y in range(127):
    for x in range(127):
        nw = y*128+x
        faces.extend([(nw, nw+128, nw+1), (nw+1, nw+128, nw+129)])
uvs = [(index % 128 / 128, 1-(index//128)/128) for face in faces for index in face]
terrain = mesh_object('Exact native terrain', vertices, faces, uvs, [terrain_material], [0]*len(faces))
water_material = material('water margin', out / 'materials/water.png')
mesh_object('Water outside final sampled row', [(-256,-256,-.01),(256,-256,-.01),(256,256,-.01),(-256,256,-.01)],
            [(0,1,2,3)], [(0,0),(128,0),(128,128),(0,128)], [water_material], [0])

materials = {name: material(name, record['path']) for name, record in data['materials'].items()}
for model in data['bmodels']:
    vertices = [tuple(v[a]/128 for a in 'xyz') for v in model['vertices']]
    faces, uvs, indices, slots = [], [], [], []
    for face in model['faces']:
        if face['attributes'] & 0x2000 or len(face['vertex_indices']) < 3:
            continue
        name = face['texture_name'].lower()
        if name not in slots:
            slots.append(name)
        width, height = data['materials'][name]['logical_size']
        faces.append(tuple(face['vertex_indices']))
        uvs.extend(((u+face['texture_delta_u'])/width, 1-(v+face['texture_delta_v'])/height)
                   for u,v in zip(face['texture_us'],face['texture_vs']))
        indices.append(slots.index(name))
    mesh_object(f'BModel {model["index"]}: {model["name"]}', vertices, faces, uvs,
                [materials[name] for name in slots], indices)

camera_data = bpy.data.cameras.new('Exact minimap bounds')
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 512
camera_data.clip_start = .1
camera_data.clip_end = 2000
camera = bpy.data.objects.new('Exact minimap bounds', camera_data)
scene.collection.objects.link(camera)
camera.location = (0, 0, 700)
camera.rotation_euler = (0, 0, 0)  # Camera -Z looks down; camera +Y is map north.
scene.camera = camera
sun_data = bpy.data.lights.new('Minimap northwest sun', 'SUN')
sun_data.energy = 1.7
sun_data.angle = .18
sun = bpy.data.objects.new('Minimap northwest sun', sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (.45, -.5, -.5)
bpy.context.view_layer.update()
errors = []
for model in data['bmodels']:
    for vertex in model['vertices']:
        point = Vector(tuple(vertex[a]/128 for a in 'xyz'))
        projected = world_to_camera_view(scene, camera, point)
        expected = ((vertex['x']+32768)/65536, (vertex['y']+32768)/65536)
        errors.append(max(abs(projected.x-expected[0]), abs(projected.y-expected[1]))*1024)
assert max(errors) < .001
metadata = dict(scene=scene.name, blender=bpy.app.version_string, camera=dict(position=list(camera.location),
    rotation=list(camera.rotation_euler), ortho_scale=camera_data.ortho_scale, units_per_blender_unit=128),
    resolution=[2048,2048], model_count=len(data['bmodels']), vertex_controls=len(errors),
    max_projection_error_x2_pixels=max(errors), geometry_moved=False,
    limitations=['No actors or decoration billboards; static terrain and BModels.',
                 'Water uses one texture frame; neutral Blender lighting, not runtime baked lighting.',
                 'The final 512-unit south/east margin beyond the 127-cell terrain uses a water plane.'])
(out / 'blender_capture.json').write_text(json.dumps(metadata, indent=2)+'\n')
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
        area.spaces.active.overlay.show_overlays = False
scene.render.filepath = str(out / 'blender_master.png')
# Save only this independent scene and its dependencies; do not rename/save the user's open project.
bpy.data.libraries.write(str(out / 'new_sorpigal.blend'), {scene}, path_remap='RELATIVE_ALL')
bpy.ops.render.render(write_still=True)
for polygon in terrain.data.polygons:
    polygon.use_smooth = True
scene.view_settings.exposure = .5
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .8
scene.render.filepath = str(out / 'blender_smooth_master.png')
bpy.ops.render.render(write_still=True)
print('Rendered New Sorpigal minimap:', metadata)
