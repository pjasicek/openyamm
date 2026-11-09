"""Review actual portable GLB, not a Blender-only rig: fixed front/profile poses and normal-speed playback."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

stage = Path(__file__).resolve().parent
scene = bpy.context.scene
scene.render.fps = 48
bpy.ops.import_scene.gltf(filepath=str(stage / 'mm6_demon_animated.glb'))
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
mesh = next(o for o in scene.objects if o.type == 'MESH' and o.name.startswith('Demon_Native_Mesh'))
for obj in scene.objects:
    if obj.type == 'MESH' and obj != mesh:
        obj.hide_render = True
rig.animation_data.action = None
for obj in scene.objects:
    for owner in (obj, obj.data.shape_keys if obj.type == 'MESH' else None):
        if owner is not None and owner.animation_data:
            owner.animation_data.action = None
            for track in owner.animation_data.nla_tracks:
                track.mute = track.name != 'Cast_FireBolt'
camera_data = bpy.data.cameras.new('Review_Camera')
camera = bpy.data.objects.new('Review_Camera', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 2.05
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 600
scene.render.resolution_y = 660
scene.render.resolution_percentage = 100
scene.world.color = (.18, .18, .18)
scene.view_settings.view_transform = 'Standard'
for name, position, power, size in [('Key', (-3, -4, 5), 700, 4), ('Fill', (3, -2, 3), 450, 3)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = position
    light.rotation_euler = (Vector((0, -.15, 1)) - light.location).to_track_quat('-Z', 'Y').to_euler()
out = stage / 'review'
out.mkdir(exist_ok=True)
for view, eye in [('front', (0, -5, 1.05)), ('profile', (5, 0, 1.05))]:
    camera_data.ortho_scale = 2.45 if view == 'profile' else 2.05
    camera.location = eye
    camera.rotation_euler = (Vector((0, -.13, .86)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    for frame in [0, 9, 18, 30, 40, 48]:
        scene.frame_set(frame)
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = str(out / f'cast_{frame:02d}_{view}.png')
        bpy.ops.render.render(write_still=True)
camera.location = (2.5, -5, 1.25)
camera_data.ortho_scale = 2.05
camera.rotation_euler = (Vector((0, -.13, .86)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.resolution_x = 400
scene.render.resolution_y = 440
scene.frame_start = 0
scene.frame_end = 48
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(out / 'playback_')
bpy.ops.render.render(animation=True)
(stage / 'review.json').write_text(json.dumps({'clip': 'Cast_FireBolt', 'frames': [0, 9, 18, 30, 40, 48],
    'fps': 48, 'source': 'mm6_demon_animated.glb', 'socket_nodes': ['Socket_Eye_Left', 'Socket_Eye_Right',
    'Socket_Palm_Left', 'Socket_Palm_Right']}, indent=2) + '\n')
