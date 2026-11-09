"""Revise only the native Attack's right leg/foot; retain the corrected upper body."""
import bpy
import hashlib
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

STAGE = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation_v3')
PREVIOUS = STAGE.parent / 'attack_animation_v2'
SOURCE = np.load(PREVIOUS / 'source_geometry.npz')
YAW_ANCHORS_DEG = [0, -2, -3, 12, 14, 0]
CHANGED_BONES = ['mixamorig:RightUpLeg', 'mixamorig:RightLeg', 'mixamorig:RightFoot']


def update():
    bpy.context.view_layer.update()


def assign(bone, orientation, position):
    matrix = orientation.to_matrix().to_4x4()
    matrix.translation = position
    bone.matrix = matrix
    update()


def solve_leg(rig, target, foot_orientation, yaw):
    upper, lower, foot = [rig.pose.bones[name] for name in CHANGED_BONES]
    upper_rest, lower_rest, foot_rest = [b.bone.matrix_local for b in (upper, lower, foot)]
    upper_vector = lower_rest.translation - upper_rest.translation
    lower_vector = foot_rest.translation - lower_rest.translation
    l1, l2 = upper_vector.length, lower_vector.length
    hip = upper.head.copy()
    delta = target - hip
    distance = delta.length
    assert abs(l1 - l2) < distance < l1 + l2
    axis = delta.normalized()
    # A modest knee turn follows the foot; the original body dip supplies flex.
    forward = Quaternion((0, 0, 1), yaw * .35) @ Vector((0, -1, 0))
    pole = (forward - axis * forward.dot(axis)).normalized()
    along = (l1 * l1 - l2 * l2 + distance * distance) / (2 * distance)
    knee = hip + axis * along + pole * math.sqrt(max(0, l1 * l1 - along * along))
    assign(upper, upper_vector.rotation_difference(knee - hip) @ upper_rest.to_quaternion(), hip)
    assign(lower, lower_vector.rotation_difference(target - knee) @ lower_rest.to_quaternion(), knee)
    assign(foot, foot_orientation, target)
    for bone in (upper, lower, foot):
        bone.location = (0, 0, 0)
        bone.scale = (1, 1, 1)
    update()


def yaw_at(frame):
    index = min(int(frame // 6), 5)
    next_index = min(index + 1, 5)
    u = max(0, min(1, (frame - index * 6) / 6))
    ease = u * u * (3 - 2 * u)
    return math.radians(YAW_ANCHORS_DEG[index] * (1 - ease) + YAW_ANCHORS_DEG[next_index] * ease)


if 'MM6_Demon_Attack_v3' in bpy.data.scenes:
    scene = bpy.data.scenes['MM6_Demon_Attack_v3']
    rig = scene.objects['Demon_Attack_v3_Rig']
    mesh = scene.objects['Demon_Attack_v3_Mesh']
    baseline = bpy.data.actions['Demon_Native_Attack_v2']
else:
    original = bpy.data.scenes['MM6_Demon_Attack']
    original_rig = original.objects['Demon_Attack_Rig']
    original_mesh = original.objects['Demon_Attack_Mesh']
    baseline = original_rig.animation_data.action
    assert baseline.name == 'Demon_Native_Attack_v2'
    scene = original.copy()
    scene.name = 'MM6_Demon_Attack_v3'
    for obj in list(scene.objects):
        scene.collection.objects.unlink(obj)
    rig = original_rig.copy()
    rig.data = original_rig.data.copy()
    rig.name = 'Demon_Attack_v3_Rig'
    mesh = original_mesh.copy()
    mesh.data = original_mesh.data.copy()
    mesh.name = 'Demon_Attack_v3_Mesh'
    mesh.parent = rig
    for modifier in mesh.modifiers:
        if modifier.type == 'ARMATURE':
            modifier.object = rig
    scene.collection.objects.link(rig)
    scene.collection.objects.link(mesh)
    camera = original.camera.copy()
    camera.data = original.camera.data.copy()
    camera.name = 'DemonAttackCamera_v3'
    scene.collection.objects.link(camera)
    scene.camera = camera

bpy.context.window.scene = scene
rig.hide_set(False)
mesh.hide_set(False)
scene.render.fps = 48
for track in rig.animation_data.nla_tracks:
    track.mute = True
rig.animation_data.action = baseline
rig.animation_data.action_slot = baseline.slots[0]
scene.frame_set(0)
foot = rig.pose.bones['mixamorig:RightFoot']
rigid = SOURCE['weights'][:, list(SOURCE['group_names']).index(foot.name)] > .999
sole_points = SOURCE['vertices'][rigid]
# The pivot lies under the medial support area, slightly ahead of the ankle. A
# world-Z rotation retains the source foot's height and avoids toe curling/roll.
pivot = foot.head.copy()
pivot.y -= .055
pivot.z = .002
baseline_samples, revised_samples, world_before, world_after = [], [], [], []
control_records = []
for frame in range(37):
    scene.frame_set(frame)
    before = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
    before_world = {b.name: b.matrix.copy() for b in rig.pose.bones}
    baseline_samples.append(before)
    world_before.append(before_world)
    foot_matrix = foot.matrix.copy()
    yaw = yaw_at(frame)
    rotation = Quaternion((0, 0, 1), yaw)
    target = pivot + rotation @ (foot_matrix.translation - pivot)
    orientation = rotation @ foot_matrix.to_quaternion()
    solve_leg(rig, target, orientation, yaw)
    after = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
    after_world = {b.name: b.matrix.copy() for b in rig.pose.bones}
    for name in before:
        if name not in CHANGED_BONES:
            assert np.max(np.abs(np.array(before[name]) - np.array(after[name]))) < 1e-7, name
    revised_samples.append(after)
    world_after.append(after_world)
    control_records.append({'frame': frame, 'yaw_degrees': math.degrees(yaw),
                            'knee_follow_degrees': math.degrees(yaw * .35),
                            'ankle_target': list(target)})

old_action = bpy.data.actions.get('Demon_Native_Attack_v3')
if old_action:
    rig.animation_data.action = baseline
    for track in rig.animation_data.nla_tracks:
        if track.name == 'Attack':
            track.strips[0].action = baseline
    bpy.data.actions.remove(old_action)
action = baseline.copy()
action.name = 'Demon_Native_Attack_v3'
bag = action.layers[0].strips[0].channelbag(action.slots[0])
for bone_name in CHANGED_BONES:
    values = [sample[bone_name].decompose() for sample in revised_samples]
    quaternions = []
    for _, quaternion, _ in values:
        if quaternions and quaternion.dot(quaternions[-1]) < 0:
            quaternion.negate()
        quaternions.append(quaternion.copy())
    for prop, vectors in [('location', [v[0] for v in values]), ('rotation_quaternion', quaternions),
                          ('scale', [Vector((1, 1, 1)) for _ in values])]:
        path = 'pose.bones[' + json.dumps(bone_name) + '].' + prop
        for component in range(len(vectors[0])):
            curve = next(c for c in bag.fcurves if c.data_path == path and c.array_index == component)
            assert len(curve.keyframe_points) == 37
            for point, frame, vector in zip(curve.keyframe_points, range(37), vectors):
                point.co = (frame, vector[component])
                point.interpolation = 'LINEAR'
            curve.update()
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
action.use_fake_user = True
for track in rig.animation_data.nla_tracks:
    if track.name == 'Attack':
        track.strips[0].action = action
        track.strips[0].action_slot = action.slots[0]
    track.mute = True
scene.frame_start = 0
scene.frame_end = 36
scene.frame_set(24)
names = [b.name for b in rig.pose.bones]
np.savez_compressed(STAGE / 'attack_baked_matrices.npz', times=np.arange(37) / 48,
                    bone_names=np.array(names),
                    basis=np.array([[np.array(s[n]) for n in names] for s in revised_samples]))
report = {
    'native_evidence': '../attack_study/feet_review_20261004/README.md',
    'source_package': '../attack_animation_v2/mm6_demon_attack.blend',
    'changed_bones': CHANGED_BONES,
    'yaw_at_native_anchor_frames_degrees': YAW_ANCHORS_DEG,
    'native_anchor_frames': [0, 6, 12, 18, 24, 30],
    'pivot_model_coordinates': list(pivot),
    'knee_yaw_share': .35,
    'joint_angles_are_restrained_3d_inferences': True,
    'pelvis_dip_and_left_leg_flex': 'Retained exactly from revision 2',
    'no_separate_toe_curl_or_foot_roll': True,
    'no_mesh_or_weight_changes': True,
    'preserved_file_sha256': {str(p.relative_to(STAGE.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in [PREVIOUS / 'mm6_demon_attack.blend', PREVIOUS / 'mm6_demon_attack.glb']},
    'samples': control_records,
}
(STAGE / 'foot_controls.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.data.libraries.write(str(STAGE / 'attack_authored_checkpoint.blend'), {scene}, path_remap='RELATIVE')
print(json.dumps({k: report[k] for k in ['changed_bones', 'yaw_at_native_anchor_frames_degrees',
                                       'pivot_model_coordinates', 'pelvis_dip_and_left_leg_flex']}, indent=2))
