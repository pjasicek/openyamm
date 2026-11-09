import bpy
import json
from pathlib import Path
from mathutils import Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_rig_review')
scene = bpy.data.scenes['MM6_Demon_Rig_Repair']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Rig_Review']
obj = scene.objects['Demon_Rigged_Review']
camera = scene.camera
scene.render.resolution_x = 640
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
frames_dir = stage / 'review_frames'
frames_dir.mkdir(exist_ok=True)
for clip, end in [('Walking', 25), ('Running', 16)]:
    action = bpy.data.actions[clip]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    for frame in range(end + 1):
        scene.frame_set(frame * 2)
        for view, direction in [('front', (1.2, -3, .35)), ('side', (3, -.4, .35))]:
            center = Vector((0, -.03, .81))
            camera.data.ortho_scale = 2.05
            camera.location = center + Vector(direction) * 2
            camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
            scene.render.filepath = str(frames_dir / (clip.lower() + '_' + view + '_' + f'{frame:02d}' + '.png'))
            bpy.ops.render.render(write_still=True)
    print('Rendered every native key pose from two directions:', clip)

# Only the corrected rig and mesh are selected. Review cameras, floor, the
# untouched comparison rig and other pre-existing scenes are excluded.
for item in scene.objects:
    item.select_set(False)
rig.hide_set(False)
obj.hide_set(False)
rig.select_set(True)
obj.select_set(True)
bpy.context.view_layer.objects.active = rig
rig.data.pose_position = 'POSE'
scene.render.fps = 48
bpy.ops.export_scene.gltf(
    filepath=str(stage / 'mm6_demon_rig_corrected.glb'), export_format='GLB',
    use_selection=True, use_active_scene=True, export_animations=True,
    export_animation_mode='NLA_TRACKS', export_frame_range=False,
    export_force_sampling=True, export_frame_step=1,
    export_all_influences=True, export_def_bones=False,
    export_optimize_animation_size=False, export_materials='NONE',
    export_normals=True, export_yup=True, export_cameras=False, export_lights=False,
)
print('Exported corrected model and both named clips')
