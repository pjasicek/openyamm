"""Reimport actual exports for windup comparisons and a full 48 fps attack sequence."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

stage = Path(__file__).resolve().parent
scene = bpy.context.scene
scene.render.fps = 48
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 600
scene.render.resolution_y = 660
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world.color = (.18, .18, .18)
scene.view_settings.view_transform = 'Standard'
for obj in list(scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
camera_data = bpy.data.cameras.new('Review_Camera')
camera = bpy.data.objects.new('Review_Camera', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 2.55
for name, position, power in [('Key', (-3, -4, 5), 700), ('Fill', (3, -2, 3), 450)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = 4
    light = bpy.data.objects.new(name, data)
    scene.collection.objects.link(light)
    light.location = position
    light.rotation_euler = (Vector((0, -.15, 1)) - light.location).to_track_quat('-Z', 'Y').to_euler()
out = stage / 'review'
out.mkdir(exist_ok=True)
reports = []
for label, path in [('before', stage.parent / 'animation_controller_20261006/mm6_demon_animated.glb'),
                    ('after', stage / 'mm6_demon_runtime.glb')]:
    existing = set(scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = set(scene.objects) - existing
    rig = next(o for o in imported if o.type == 'ARMATURE')
    for obj in imported:
        if obj.type == 'MESH' and not obj.name.startswith('Demon_Native_Mesh'):
            obj.hide_render = True
        for owner in (obj, obj.data.shape_keys if obj.type == 'MESH' else None):
            if owner is not None and owner.animation_data:
                owner.animation_data.action = None
                for track in owner.animation_data.nla_tracks:
                    track.mute = track.name != 'Attack'
    for frame in [0, 6, 12, 18, 24, 30, 36]:
        scene.frame_set(frame)
        wrist = rig.pose.bones['mixamorig:RightHand'].head
        reports.append({'version': label, 'frame': frame, 'wrist': list(wrist)})
        camera.location = (0, -5, 1)
        camera.rotation_euler = (Vector((0, -.13, 1)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(out / f'{label}_{frame:02d}_front.png')
        bpy.ops.render.render(write_still=True)
    camera.location = (5, 0, 1)
    camera.rotation_euler = (Vector((0, -.13, 1)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.frame_set(12)
    scene.render.filepath = str(out / f'{label}_12_profile.png')
    bpy.ops.render.render(write_still=True)
    if label == 'after':
        camera.location = (2.5, -5, 1.15)
        camera.rotation_euler = (Vector((0, -.13, 1)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.resolution_x = 400
        scene.render.resolution_y = 440
        scene.frame_start, scene.frame_end = 0, 35
        scene.render.filepath = str(out / 'playback_')
        bpy.ops.render.render(animation=True)
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
(stage / 'review.json').write_text(json.dumps({'source': 'mm6_demon_runtime.glb', 'clip': 'Attack',
    'fps': 48, 'frames': reports, 'playback_frames': 36, 'playback_seconds': .75}, indent=2) + '\n')
