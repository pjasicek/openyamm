"""Export the checked Attack revision without altering previous deliverables."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

stage = Path(__file__).resolve().parent
review = json.loads((stage / 'foot_deformation_review.json').read_text())['summary']
assert review['samples'] == 145 and review['keyed_poses'] == 37
assert review['maximum_preserved_bone_world_error'] == 0
assert review['maximum_left_foot_change'] == 0
assert review['minimum_sole_height'] > 0
assert review['maximum_sole_height_change'] < .0002
assert review['maximum_leg_segment_length_relative_error'] < 1e-5
assert review['maximum_rigid_foot_edge_length_relative_error'] < .0001
bpy.ops.wm.open_mainfile(filepath=str(stage / 'attack_authored_checkpoint.blend'))
scene = bpy.data.scenes['MM6_Demon_Attack_v3']
scene.name = 'MM6_Demon_Attack'
bpy.context.window.scene = scene
rig = scene.objects['Demon_Attack_v3_Rig']
mesh = scene.objects['Demon_Attack_v3_Mesh']
rig.name = 'Demon_Attack_Rig'
mesh.name = 'Demon_Attack_Mesh'
for item in scene.objects:
    item.select_set(False)
rig.hide_set(False)
mesh.hide_set(False)
rig.select_set(True)
mesh.select_set(True)
bpy.context.view_layer.objects.active = rig
rig.data.pose_position = 'POSE'
for track in rig.animation_data.nla_tracks:
    track.mute = True
scene.render.fps = 48
scene.frame_start, scene.frame_end = 0, 36
bpy.ops.export_scene.gltf(
    filepath=str(stage / 'mm6_demon_attack.glb'), export_format='GLB', use_selection=True, use_active_scene=True,
    export_animations=True, export_animation_mode='NLA_TRACKS', export_frame_range=False,
    export_force_sampling=True, export_frame_step=1, export_all_influences=True, export_def_bones=False,
    export_optimize_animation_size=False, export_materials='NONE', export_normals=True, export_yup=True,
    export_cameras=False, export_lights=False)
action = bpy.data.actions['Demon_Native_Attack_v3']
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
scene.frame_set(18)
center = Vector((0, -.10, .86))
scene.camera.data.ortho_scale = 2.35
scene.camera.location = center + Vector((0, -6, 0))
scene.camera.rotation_euler = (center - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
rig.hide_set(True)
for item in scene.objects:
    item.select_set(False)
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
bpy.data.libraries.write(str(stage / 'mm6_demon_attack.blend'), {scene}, path_remap='RELATIVE')
manifest = json.loads((stage.parent / 'attack_animation_v2/animation_manifest.json').read_text())
manifest['revision'] = 3
manifest['previous_package'] = '../attack_animation_v2/'
manifest['motion_change'] = 'Right-foot inward pivot and knee following; original pelvis dip, left-leg flex and all corrected upper-body curves preserved'
manifest['changed_bones'] = review['changed_bones']
(stage / 'animation_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Exported checked revision 3 GLB and isolated Blender project.', flush=True)
