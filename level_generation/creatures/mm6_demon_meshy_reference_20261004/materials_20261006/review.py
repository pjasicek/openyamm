"""Review actual exported material variants in front, profile and rear views."""
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
scene.render.resolution_x, scene.render.resolution_y = 600, 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world.color = (.18, .18, .18)
scene.view_settings.view_transform = 'Standard'
camera_data = bpy.data.cameras.new('Review Camera')
camera = bpy.data.objects.new('Review Camera', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type, camera_data.ortho_scale = 'ORTHO', 2.05
for name, position, power in [('Key', (-3, -4, 5), 450), ('Fill', (3, 1, 3), 250)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size = power, 'DISK', 4
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = position
    light.rotation_euler = (Vector((0, 0, 1)) - light.location).to_track_quat('-Z', 'Y').to_euler()
out = stage / 'review'
for variant, name in enumerate(('a', 'b', 'c')):
    document, binary = read_glb(stage / 'mm6_demon_runtime.glb')
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if variant in mapping['variants']:
                    primitive['material'] = mapping['material']
    selected = out / 'selected.glb'
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
    for view, position in [('front', (0, -5, 1.1)), ('profile', (5, 0, 1.1)), ('back', (0, 5, 1.1))]:
        camera.location = position
        camera.rotation_euler = (Vector((0, -.06, .86)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(out / f'{name}_{view}.png')
        bpy.ops.render.render(write_still=True)
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
    selected.unlink()
print('Rendered front/profile/back of all three exported skins.')
