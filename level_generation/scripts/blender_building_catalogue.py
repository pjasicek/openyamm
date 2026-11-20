"""Run through Blender MCP; render selected native reference BModels in an independent study scene.

Globals: MODEL_IDS=[42,...], ASSEMBLIES=['luodrin',...], REPO='/path/OpenYAMM'.
Default renders only Luodrin. Repeat small batches; existing scenes and active scene are preserved.
Sources/materials are retained in the study scene for further MCP inspection. No game/authoring sources change.
"""
from pathlib import Path
import json
import math
import sys
import bpy
from mathutils import Vector

root = Path(globals().get('REPO', '/home/pjasicek/github/OpenYAMM'))
catalogue = globals().get('CATALOGUE', 'mm8_ravenshore')
out = root / 'level_generation/catalogues' / catalogue
metadata = json.loads((out / 'catalogue.json').read_text())
sys.path.insert(0, str(root / 'util'))
from map_export import parse_odm_file
world, map_name = metadata['map'].split('/', 1)
native = parse_odm_file(root / 'assets_dev/worlds' / world / 'maps' / map_name)['payload']
texture_paths = json.loads((out / 'textures.json').read_text())
previous_scene = bpy.context.window.scene
prefix = metadata.get('object_prefix', 'RavenshoreCatalogue')
scene_name = metadata.get('study_scene', 'Ravenshore building catalogue')
owner = 'level_generation/' + catalogue
model_prefix = 'Catalogue' if catalogue == 'mm8_ravenshore' else prefix
camera_name = model_prefix + ' camera'
sun_name = model_prefix + ' sun'
scene = bpy.data.scenes.get(scene_name)
if scene is None:
    scene = bpy.data.scenes.new(scene_name)
    scene['catalogue_owner'] = owner
assert scene.get('catalogue_owner') == owner


def material(key):
    name = prefix + '_' + key.lower()
    mat = bpy.data.materials.get(name)
    if mat: return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 1
    node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(str(root / texture_paths[key.lower()]['path']), check_existing=True)
    node.interpolation = 'Closest'
    mat.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
    return mat


def model_object(index):
    name = f'{model_prefix} BModel {index:03d}'
    obj = scene.objects.get(name)
    if obj: return obj
    model = native['bmodels'][index]
    vertices = [tuple(v[k] / 128 for k in 'xyz') for v in model['vertices']]
    faces = [f for f in model['faces'] if not f['attributes'] & 0x2000]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], [f['vertex_indices'] for f in faces]); mesh.update()
    obj = bpy.data.objects.new(name, mesh); scene.collection.objects.link(obj)
    obj['native_bmodel_index'] = index; obj['native_name'] = model['name']
    slots = {}
    layer = mesh.uv_layers.new(name='Native texel UVs')
    for polygon, face in zip(mesh.polygons, faces):
        key = face['texture_name']
        mat = material(key)
        if key not in slots:
            slots[key] = len(mesh.materials); mesh.materials.append(mat)
        polygon.material_index = slots[key]
        image = next(n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE')
        width, height = image.size
        for li, u, v in zip(polygon.loop_indices, face['texture_us'], face['texture_vs']):
            layer.data[li].uv = ((u + face['texture_delta_u']) / width,
                                1 - (v + face['texture_delta_v']) / height)
    return obj


def render(name, ids, focus_event=None):
    for obj in scene.objects:
        if obj.type == 'MESH': obj.hide_render = True; obj.hide_set(True)
    vertices = []
    for index in ids:
        obj = model_object(index); obj.hide_render = False; obj.hide_set(False)
        vertices += [Vector(tuple(v[k] / 128 for k in 'xyz')) for v in native['bmodels'][index]['vertices']]
    lo = Vector(tuple(min(v[a] for v in vertices) for a in range(3)))
    hi = Vector(tuple(max(v[a] for v in vertices) for a in range(3)))
    center = (lo + hi) / 2
    entries = [f for index in ids for f in metadata['models'][index]['face_records']
               if any(f['index'] in s['active_faces'] for s in metadata['models'][index]['services'])]
    if focus_event is not None:
        entries.sort(key=lambda f: f['event'] != focus_event)
    # Prefer the first actual entrance's exterior normal; auxiliary pieces use their label-linked entry.
    if not entries:
        target_events = {s['event'] for i in ids for s in metadata['models'][i]['services']}
        entries = [f for r in metadata['models'] for f in r['face_records']
                   if f['event'] in target_events and abs(f['normal'][2]) < .5]
    direction = Vector(entries[0]['normal']) if entries else Vector((.7, -.8, 0))
    direction.z = 0
    if direction.length < .01: direction = Vector((.7, -.8, 0))
    direction.normalize()
    side = Vector((-direction.y, direction.x, 0))
    orbit = direction + side * .6 + Vector((0, 0, .7))
    extent = max(hi - lo)
    camera.location = center + orbit * max(extent * 2, 10)
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    inverse = camera.rotation_euler.to_quaternion().inverted()
    projected = [inverse @ (v - center) for v in vertices]
    width = max(v.x for v in projected) - min(v.x for v in projected)
    height = max(v.y for v in projected) - min(v.y for v in projected)
    offset = camera.rotation_euler.to_quaternion() @ Vector(((max(v.x for v in projected) + min(v.x for v in projected)) / 2,
                                                            (max(v.y for v in projected) + min(v.y for v in projected)) / 2, 0))
    center += offset
    camera.location += offset
    camera.data.ortho_scale = max(width, height * scene.render.resolution_x / scene.render.resolution_y) * 1.22
    scene.objects[sun_name].rotation_euler = (-orbit).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(out / 'images' / (name + '.png'))
    bpy.ops.render.render(write_still=True)
    report = dict(models=ids, source='native ODM vertices/faces/UVs', lighting='neutral study, no terrain/actors',
                  view='isolated oblique, independently fitted; compare numeric dimensions for scale',
                  camera_position=list(camera.location), camera_target=list(center), scale=128,
                  focus_event=focus_event)
    (out / 'images' / (name + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    print('CATALOGUE_RENDER', name, ids)


try:
    bpy.context.window.scene = scene
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 8; scene.cycles.use_denoising = True
    scene.render.resolution_x = 800; scene.render.resolution_y = 650; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'Standard'
    if scene.world is None:
        scene.world = bpy.data.worlds.new(model_prefix + ' neutral world'); scene.world.use_nodes = True
        scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.12, .14, .18, 1)
        scene.world.node_tree.nodes['Background'].inputs[1].default_value = .8
    camera = scene.objects.get(camera_name)
    if camera is None:
        data = bpy.data.cameras.new(camera_name); camera = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(camera); camera.data.clip_end = 10000
        data = bpy.data.lights.new(sun_name, 'SUN'); data.energy = 2; data.angle = .2
        sun = bpy.data.objects.new(data.name, data); scene.collection.objects.link(sun)
        sun.rotation_euler = (.3, -.4, -.5)
    scene.camera = camera
    for index in globals().get('MODEL_IDS', [42]): render(f'{index:03d}', [index])
    for key in globals().get('ASSEMBLIES', []):
        assembly = next(a for a in metadata['assembly_views'] if a['id'] == key)
        render('assembly_' + key, assembly['models'], assembly.get('focus_event'))
finally:
    bpy.context.window.scene = previous_scene
print('Restored active scene:', previous_scene.name)
