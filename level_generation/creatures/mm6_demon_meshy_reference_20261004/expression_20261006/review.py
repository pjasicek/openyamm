"""Matching-camera review of the actual before/after exports, skins, lower LODs and action poses."""
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
camera_data.ortho_scale = .62
for name, position, power in [('Key', (-3, -4, 5), 450), ('Fill', (3, -2, 3), 250)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.shape, data.size = power, 'DISK', 4
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = position
    light.rotation_euler = (Vector((0, -.15, 1)) - light.location).to_track_quat('-Z', 'Y').to_euler()
clay = bpy.data.materials.new('Review_Clay')
clay.diffuse_color = (.34, .34, .34, 1)
clay.use_nodes = True
clay.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (.34, .34, .34, 1)
clay.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = .8
out = stage / 'review'
out.mkdir(exist_ok=True)


def render(label, source, variant=0, lod=0, clip='Standing', time=0, views=('front',), with_clay=False):
    document, binary = read_glb(source)
    body = next(n for n in document['nodes'] if n.get('name') == 'Demon_Native_Mesh')
    if lod:
        body['mesh'] = document['meshes'][body['mesh']]['extras']['openyamm_lods'][lod - 1]
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
                track.mute = track.name != clip
    scene.frame_set(int(time * scene.render.fps), subframe=time * scene.render.fps % 1)
    for view in views:
        position = {'front': (0, -5, 1.6), 'oblique': (3, -5, 1.6), 'profile': (5, -.13, 1.6)}[view]
        camera.location = position
        target = (0, -.33, 1.57) if view == 'profile' else (0, -.13, 1.57)
        camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(out / f'{label}_{view}.png')
        bpy.ops.render.render(write_still=True)
        if with_clay:
            scene.view_layers[0].material_override = clay
            scene.render.filepath = str(out / f'{label}_{view}_clay.png')
            bpy.ops.render.render(write_still=True)
            scene.view_layers[0].material_override = None
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
    selected.unlink()


render('before_a', stage.parent / 'variants_20261006/mm6_demon_runtime.glb',
       views=('front', 'oblique', 'profile'), with_clay=True)
render('after_a', stage / 'mm6_demon_runtime.glb', views=('front', 'oblique', 'profile'), with_clay=True)
for variant, name in ((1, 'b'), (2, 'c')):
    render('after_' + name, stage / 'mm6_demon_runtime.glb', variant=variant)
for lod in (1, 2, 3):
    render('after_lod' + str(lod), stage / 'mm6_demon_runtime.glb', lod=lod)
render('before_lod1', stage.parent / 'variants_20261006/mm6_demon_runtime.glb', lod=1)
render('after_lod1_rest', stage / 'mm6_demon_runtime.glb', lod=1, clip='Rest')
for clip, time in (('Attack', .375), ('Hit', .25), ('Cast_FireBolt', .5)):
    render(clip, stage / 'mm6_demon_runtime.glb', clip=clip, time=time, views=('oblique',))
print('Reviewed matching clay/material cameras, all three skins, four LODs and representative action poses.')
