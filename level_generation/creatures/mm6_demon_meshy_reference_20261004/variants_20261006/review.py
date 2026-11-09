"""Review each skin from the delivered GLB using the same material mapping as the runtime."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

stage = Path(__file__).resolve().parent
sys.path.insert(0, str(stage.parents[3] / 'tools'))
from build_actor_lods import read_glb, write_glb

scene = bpy.context.scene
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 480, 600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world.color = (.18, .18, .18)
scene.view_settings.view_transform = 'Standard'
camera_data = bpy.data.cameras.new('Camera')
camera = bpy.data.objects.new('Camera', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
for name, position, power in [('Key', (-3, -4, 5), 450), ('Fill', (3, -2, 3), 250)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size = power, 'DISK', 4
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = position
    light.rotation_euler = (Vector((0, -.15, 1)) - light.location).to_track_quat('-Z', 'Y').to_euler()
out = stage / 'review'
out.mkdir(exist_ok=True)
for variant, name in enumerate(('demon_a', 'demon_b', 'demon_c')):
    document, binary = read_glb(stage / 'mm6_demon_runtime.glb')
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            mappings = primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
            for mapping in mappings:
                if variant in mapping['variants']:
                    primitive['material'] = mapping['material']
    selected = out / f'{name}_selected.glb'
    write_glb(selected, document, binary)
    existing = set(scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(selected))
    imported = set(scene.objects) - existing
    for obj in imported:
        if obj.type == 'MESH' and not obj.name.startswith('Demon_Native_Mesh'):
            obj.hide_render = True
        if obj.animation_data:
            obj.animation_data.action = None
            for track in obj.animation_data.nla_tracks:
                track.mute = track.name != 'Standing'
    scene.frame_set(0)
    for view, position, target, size in [
        ('front', (0, -5, 1), (0, -.13, .85), 2.3),
        ('profile', (5, 0, 1), (0, -.13, .85), 2.3),
        ('back', (0, 5, 1), (0, -.13, .85), 2.3),
        ('face', (0, -5, 1.6), (0, -.13, 1.57), .62)]:
        camera.location = position
        camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera_data.ortho_scale = size
        scene.render.filepath = str(out / f'{name}_{view}.png')
        bpy.ops.render.render(write_still=True)
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
print('Rendered twelve matching-camera views of the actual A/B/C material variants.')
