"""Run in Blender with REPO set; append an independent scene and render two layers."""
import hashlib
import json
import math
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

root = Path(REPO)
here = root / 'level_generation/ui/hud_inventory/minimap_study_20260927'
out = here / 'new_sorpigal'
recipe = json.loads((here / 'vinevi_recipe.json').read_text())
data = json.loads((out / 'scene_data.json').read_text())

# Appending, rather than copying references from the live scene, protects its meshes and materials.
with bpy.data.libraries.load(str(out / 'new_sorpigal.blend'), link=False) as (available, loaded):
    assert len(available.scenes) == 1
    loaded.scenes = list(available.scenes)
scene = loaded.scenes[0]
scene.name = 'New Sorpigal - vinevi process'
bpy.context.window.scene = scene
assert scene.render.engine == 'CYCLES'
scene.cycles.samples = recipe['render']['samples']
scene.cycles.seed = recipe['render']['seed']
scene.cycles.use_denoising = recipe['render']['denoising']
scene.cycles.diffuse_bounces = recipe['render']['diffuse_bounces']
scene.render.resolution_x = scene.render.resolution_y = recipe['render']['size']
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
assert 'RGBA' in [i.identifier for i in scene.render.image_settings.bl_rna.properties['color_mode'].enum_items]
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1

world_node = next(node for node in scene.world.node_tree.nodes if node.type == 'BACKGROUND')
world_node.inputs['Color'].default_value = (*recipe['world']['color_linear_rgb'], 1)
world_node.inputs['Strength'].default_value = recipe['world']['strength']
sun = next(obj for obj in scene.objects if obj.type == 'LIGHT')
sun.data.color = recipe['sun']['color_linear_rgb']
sun.data.energy = recipe['sun']['strength']
sun.data.use_shadow = False
azimuth = math.radians(recipe['sun']['azimuth_degrees_clockwise_from_north'])
elevation = math.radians(recipe['sun']['elevation_degrees'])
to_sun = Vector((math.sin(azimuth)*math.cos(elevation),
                 math.cos(azimuth)*math.cos(elevation), math.sin(elevation)))
sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()

terrain_collection = bpy.data.collections.new('Vinevi terrain')
objects_collection = bpy.data.collections.new('Vinevi buildings')
scene.collection.children.link(terrain_collection)
scene.collection.children.link(objects_collection)
terrain = next(obj for obj in scene.objects if obj.name.startswith('Exact native terrain'))
for polygon in terrain.data.polygons:
    polygon.use_smooth = True
terrain.data.update()
# Retain a little native triangle definition without moving any terrain vertex.
normal_blend = recipe['terrain_flat_normal_blend']
normals = [normal.vector.copy() for normal in terrain.data.corner_normals]
for polygon in terrain.data.polygons:
    for loop_index in polygon.loop_indices:
        normals[loop_index] = normals[loop_index].lerp(polygon.normal, normal_blend).normalized()
terrain.data.normals_split_custom_set(normals)
for obj in list(scene.objects):
    if obj.type != 'MESH':
        continue
    obj.visible_shadow = False
    collection = objects_collection if obj.name.startswith('BModel ') else terrain_collection
    collection.objects.link(obj)
    scene.collection.objects.unlink(obj)

terrain_layer = scene.view_layers[0]
terrain_layer.name = 'Terrain'
terrain_layer.layer_collection.children[objects_collection.name].exclude = True
objects_layer = scene.view_layers.new('Objects')
# Terrain still occludes buried model parts, but contributes no color to the object layer.
objects_layer.layer_collection.children[terrain_collection.name].holdout = True
bpy.context.view_layer.update()

errors = []
for model in data['bmodels']:
    for vertex in model['vertices']:
        position = Vector(tuple(vertex[axis]/128 for axis in 'xyz'))
        uv = world_to_camera_view(scene, scene.camera, position)
        expected = ((vertex['x']+32768)/65536, (vertex['y']+32768)/65536)
        errors.append(max(abs(uv.x-expected[0]), abs(uv.y-expected[1]))*1024)
assert max(errors) < .001
models = [obj for obj in objects_collection.objects if obj.type == 'MESH']
assert len(models) == len(data['bmodels']) == 85
max_vertex_error = 0
for obj in models:
    index = int(obj.name.split(':')[0].split()[1])
    model = data['bmodels'][index]
    assert len(obj.data.vertices) == len(model['vertices'])
    for actual, expected in zip(obj.data.vertices, model['vertices']):
        expected = Vector(tuple(expected[axis]/128 for axis in 'xyz'))
        max_vertex_error = max(max_vertex_error, (obj.matrix_world @ actual.co - expected).length)
assert max_vertex_error == 0
assert len(terrain.data.vertices) == 128*128
for index, vertex in enumerate(terrain.data.vertices):
    y, x = divmod(index, 128)
    expected = Vector(((x-64)*4, (64-y)*4, data['height_map'][index]/4))
    assert (terrain.matrix_world @ vertex.co - expected).length == 0

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
        area.spaces.active.overlay.show_overlays = False

metadata = dict(recipe=recipe, scene=scene.name, blender=bpy.app.version_string,
    camera=dict(position=list(scene.camera.location), rotation=list(scene.camera.rotation_euler),
                ortho_scale=scene.camera.data.ortho_scale, world_units_per_blender_unit=128),
    vertex_controls=len(errors), max_projection_error_x2_pixels=max(errors),
    max_model_vertex_error_blender_units=max_vertex_error, terrain_vertices_unchanged=True,
    cast_shadows=False, terrain_occludes_objects=True, model_count=len(models),
    color_management=dict(view=scene.view_settings.view_transform, look=scene.view_settings.look,
                          exposure=scene.view_settings.exposure, gamma=scene.view_settings.gamma),
    base_scene_sha256=hashlib.sha256((out/'new_sorpigal.blend').read_bytes()).hexdigest(),
    limitations=['Numeric settings are chosen here; the author did not publish values in the tutorial.',
                 'The linked Krita project returned HTTP 403 and could not be inspected.',
                 'Current restored textures; no decoration billboards or actors.',
                 'Terrain normals blend 85% smooth and 15% face normals; geometry and map bounds are retained.'])
for layer, filename in [(terrain_layer, 'vinevi_terrain_master.png'),
                        (objects_layer, 'vinevi_objects_master.png')]:
    for candidate in scene.view_layers:
        candidate.use = candidate == layer
    bpy.context.window.view_layer = layer
    scene.render.filepath = str(out / filename)
    bpy.ops.render.render(write_still=True)
    print('Completed', filename, flush=True)

for layer in scene.view_layers:
    layer.use = True
bpy.context.window.view_layer = terrain_layer
bpy.data.libraries.write(str(out / 'new_sorpigal_vinevi.blend'), {scene}, path_remap='RELATIVE_ALL')
(out / 'vinevi_capture.json').write_text(json.dumps(metadata, indent=2)+'\n')
print('Completed vinevi capture:', json.dumps(metadata), flush=True)
