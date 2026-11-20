import bpy
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_rig_review')
scene = bpy.data.scenes['MM6_Demon_Rig_Repair']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Rig_Review']
obj = scene.objects['Demon_Rigged_Review']
rig.data.pose_position = 'POSE'
for track in rig.animation_data.nla_tracks:
    track.mute = True

def smoothstep(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3 - 2 * t)

def assign_matrix(bone, rotation, position):
    matrix = rotation.to_matrix().to_4x4()
    matrix.translation = position
    bone.matrix = matrix
    bpy.context.view_layer.update()

def solve_leg(side, source, target, rotation):
    upper = rig.pose.bones['mixamorig:' + side + 'UpLeg']
    lower = rig.pose.bones['mixamorig:' + side + 'Leg']
    foot = rig.pose.bones['mixamorig:' + side + 'Foot']
    h, k, a = (source[bone.name].translation for bone in (upper, lower, foot))
    first, second = k - h, a - k
    l1, l2 = first.length, second.length
    direction = target - h
    distance = direction.length
    assert distance < l1 + l2 - 1e-5, {'side': side, 'unreachable_ankle': distance, 'leg_length': l1 + l2}
    direction.normalize()
    bend = first - direction * first.dot(direction)
    bend.normalize()
    along = (l1 * l1 - l2 * l2 + distance * distance) / (2 * distance)
    knee = h + direction * along + bend * math.sqrt(max(0.0, l1 * l1 - along * along))
    assign_matrix(upper, first.rotation_difference(knee - h) @ source[upper.name].to_quaternion(), h)
    assign_matrix(lower, second.rotation_difference(target - knee) @ source[lower.name].to_quaternion(), knee)
    assign_matrix(foot, rotation @ foot.bone.matrix_local.to_quaternion(), target)
    error = (foot.head - target).length
    assert error < 2e-6, {'side': side, 'foot_head_error': error}

# Reset to the original unmodified clips when resuming this correction.
for clip in ('Walking', 'Running'):
    action = bpy.data.actions.get(clip + '_PlacementSource')
    if action is None:
        action = bpy.data.actions[clip].copy()
        action.name = clip + '_PlacementSource'
        action.use_fake_user = True

foot_points = {}
for side in ('Left', 'Right'):
    foot_name = 'mixamorig:' + side + 'Foot'
    foot_group = obj.vertex_groups[foot_name].index
    # The fully rigid foot vertices include every claw and the underside of the
    # forefoot. The soft ankle seam is deliberately excluded from contact tests.
    foot_points[side] = [vertex.co - rig.data.bones[foot_name].head_local
                        for vertex in obj.data.vertices
                        if sum(entry.weight for entry in vertex.groups if entry.group == foot_group) > .999]

report = {}
for clip, end in [('Walking', 25), ('Running', 16)]:
    action = bpy.data.actions[clip + '_PlacementSource']
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    samples = []
    # Half-native-frame keys become integer keys at 48 fps, preserving duration.
    for time in np.arange(0, end + .25, .5):
        scene.frame_set(int(time), subframe=float(time % 1))
        matrices = {bone.name: bone.matrix.copy() for bone in rig.pose.bones}
        original_basis = {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}
        contact_rows = {}
        targets = {}
        for side in ('Left', 'Right'):
            foot = rig.pose.bones['mixamorig:' + side + 'Foot']
            original = matrices[foot.name]
            ankle = original.translation.copy()
            skin = original @ foot.bone.matrix_local.inverted()
            euler = skin.to_euler('XYZ')
            # Preserve heading; remove the preset's persistent sideways roll.
            yaw = Quaternion((0, 0, 1), euler.z)
            # Low feet approach the ground flat. Elevated feet retain toe-off
            # pitch, including the backwards rotation during the running swing.
            clearance_blend = smoothstep(.205, .46, ankle.z)
            pitch = euler.x * clearance_blend
            rotation = yaw @ Quaternion((1, 0, 0), pitch)
            minimum = min((rotation @ point).z for point in foot_points[side])
            # For a low foot, plant the underside smoothly; for a lifted foot,
            # keep its original ankle height. A small margin also covers keys
            # between the sampled poses. Changing ankle height uses a two-bone
            # leg solve, retaining hip and ankle XY and the native bend side.
            planting = 1 - smoothstep(.215, .31, ankle.z)
            plant_height = .006 - minimum
            target_z = ankle.z * (1 - planting) + plant_height * planting
            target_z = max(target_z, plant_height)
            targets[side] = {'ankle': ankle, 'height': target_z, 'floor_height': plant_height,
                             'planting': planting, 'rotation': rotation}
            contact_rows[side] = {
                'source_ankle_height': ankle.z, 'ankle_height': target_z,
                'pitch_degrees': math.degrees(pitch), 'plant_blend': planting,
                'rigid_sole_height': target_z + minimum,
                'ankle_xy_preserved': True,
            }
        # The preset slightly overextends the legs when the broad feet are
        # planted flat. Lower the root only as much as their fixed lengths need;
        # never stretch a leg or leave a planted sole floating above the floor.
        root_lowering = 0.0
        for iteration in range(12):
            required = root_lowering
            for side, target_data in targets.items():
                h, k, a = (matrices['mixamorig:' + side + suffix].translation
                           for suffix in ('UpLeg', 'Leg', 'Foot'))
                reach = (k - h).length + (a - k).length - .002
                target_z = max(target_data['floor_height'], target_data['height']
                               - root_lowering * (1 - target_data['planting']))
                horizontal = (Vector((a.x, a.y, 0)) - Vector((h.x, h.y, 0))).length
                assert horizontal < reach, {'side': side, 'unreachable_horizontal_stride': horizontal}
                required = max(required, h.z - target_z - math.sqrt(reach * reach - horizontal * horizontal))
            if required - root_lowering < 1e-7:
                break
            root_lowering = required
        assert root_lowering < .1, {'excessive_root_adjustment': root_lowering}
        if root_lowering:
            for matrix in matrices.values():
                matrix.translation.z -= root_lowering
            rig.pose.bones['mixamorig:Hips'].matrix = matrices['mixamorig:Hips']
            bpy.context.view_layer.update()
        for side, target_data in targets.items():
            ankle = target_data['ankle']
            target_z = max(target_data['floor_height'], target_data['height']
                           - root_lowering * (1 - target_data['planting']))
            solve_leg(side, matrices, Vector((ankle.x, ankle.y, target_z)), target_data['rotation'])
            contact_rows[side]['ankle_height'] = target_z
            contact_rows[side]['rigid_sole_height'] = target_z - target_data['floor_height'] + .006
        contact_rows['root_lowering'] = root_lowering
        changed_names = ['mixamorig:' + side + suffix for side in ('Left', 'Right')
                         for suffix in ('UpLeg', 'Leg', 'Foot')]
        changed_names.append('mixamorig:Hips')
        basis = {name: (rig.pose.bones[name].matrix_basis.copy() if name in changed_names else matrix)
                 for name, matrix in original_basis.items()}
        for name in changed_names:
            loc_error = (basis[name].translation - original_basis[name].translation).length
            if name != 'mixamorig:Hips':
                assert loc_error < 3e-6, {'bone': name, 'unexpected_local_translation': loc_error}
        samples.append({'frame': float(time), 'basis': basis, 'contacts': contact_rows})
    final = bpy.data.actions.get(clip)
    # Create a fresh action, avoiding mixed source/final frame ranges on resumes.
    if final is not None:
        for track in rig.animation_data.nla_tracks:
            for strip in track.strips:
                if strip.action == final:
                    strip.action = action
        if rig.animation_data.action == final:
            rig.animation_data.action = action
        bpy.data.actions.remove(final)
    final = bpy.data.actions.new(clip)
    slot = final.slots.new(id_type='OBJECT', name=rig.name)
    layer = final.layers.new('Corrected placement')
    strip = layer.strips.new(type='KEYFRAME')
    bag = strip.channelbag(slot, ensure=True)
    for bone in rig.pose.bones:
        values = [sample['basis'][bone.name].decompose() for sample in samples]
        quaternions = []
        for _, quat, _ in values:
            if quaternions and quat.dot(quaternions[-1]) < 0:
                quat.negate()
            quaternions.append(quat.copy())
        for property_name, vectors in [('location', [value[0] for value in values]),
                                       ('rotation_quaternion', quaternions),
                                       ('scale', [value[2] for value in values])]:
            path = 'pose.bones[' + json.dumps(bone.name) + '].' + property_name
            for component in range(len(vectors[0])):
                curve = bag.fcurves.new(data_path=path, index=component)
                curve.keyframe_points.add(len(samples))
                for key, sample, vector in zip(curve.keyframe_points, samples, vectors):
                    key.co = (sample['frame'] * 2, vector[component])
                    key.interpolation = 'LINEAR'
                curve.update()
    final.use_fake_user = True
    report[clip] = {'duration_seconds': end / 24, 'baked_fps': 48, 'keyed_poses': len(samples),
                    'modified_bones': changed_names,
                    'contacts': [{'frame': sample['frame'], **sample['contacts']} for sample in samples]}
    for track in rig.animation_data.nla_tracks:
        if track.name == clip:
            track.strips[0].action = final
            track.strips[0].action_frame_start = 0
            track.strips[0].action_frame_end = end * 2
            track.strips[0].frame_start = 0
            track.strips[0].frame_end = end * 2
            track.mute = True
    rig.animation_data.action = final
    rig.animation_data.action_slot = slot
scene.render.fps = 48
scene.frame_start = 0
scene.frame_end = 50
(stage / 'foot_placement_corrections.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'rig_placement_checkpoint.blend'), copy=True)
print(json.dumps({clip: {key: value for key, value in record.items() if key != 'contacts'}
                  for clip, record in report.items()}, indent=2))
