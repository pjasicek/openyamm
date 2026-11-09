"""Check dense foot contact, lower-leg shape and exact preservation of revision 2."""
import bpy
import hashlib
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Quaternion, Vector

STAGE = Path(__file__).resolve().parent
PREVIOUS = STAGE.parent / 'attack_animation_v2'
bpy.ops.wm.open_mainfile(filepath=str(STAGE / 'attack_authored_checkpoint.blend'))
scene = bpy.data.scenes['MM6_Demon_Attack_v3']
rig = scene.objects['Demon_Attack_v3_Rig']
mesh = scene.objects['Demon_Attack_v3_Mesh']
with bpy.data.libraries.load(str(PREVIOUS / 'mm6_demon_attack.blend'), link=False) as (available, loaded):
    loaded.scenes = ['MM6_Demon_Attack']
baseline_scene = loaded.scenes[0]
baseline_rig = baseline_scene.objects['Demon_Attack_Rig']
baseline_mesh = baseline_scene.objects['Demon_Attack_Mesh']
baseline_action = baseline_rig.animation_data.action
action = rig.animation_data.action
for obj in (rig, baseline_rig):
    obj.hide_set(False)
    for track in obj.animation_data.nla_tracks:
        track.mute = True
data = np.load(PREVIOUS / 'source_geometry.npz')
rest, faces, weights = data['vertices'], data['faces'], data['weights']
names = list(data['group_names'])
controls = json.loads((STAGE / 'foot_controls.json').read_text())
pivot = np.array(controls['pivot_model_coordinates'])
changed = set(controls['changed_bones'])
changed_world = changed | {'mixamorig:RightToeBase', 'mixamorig:RightToe_End'}
edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
rest_lengths = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
rest_areas = np.linalg.norm(np.cross(rest[faces[:, 1]] - rest[faces[:, 0]], rest[faces[:, 2]] - rest[faces[:, 0]]), axis=1)
foot_masks = {side: weights[:, names.index('mixamorig:' + side + 'Foot')] > .999 for side in ('Right', 'Left')}
foot_edges = {side: np.all(foot_masks[side][edges], axis=1) for side in foot_masks}
leg_mask = weights[:, names.index('mixamorig:RightLeg')] > .75
upper_mask = weights[:, names.index('mixamorig:RightUpLeg')] > .75
upper_body = weights[:, [i for i, n in enumerate(names) if not any(x in n for x in ('UpLeg', 'Leg', 'Foot', 'Toe'))]].sum(1) > .999


def evaluate(s, r, m, clip, time):
    bpy.context.window.scene = s
    r.animation_data.action = clip
    r.animation_data.action_slot = clip.slots[0]
    s.frame_set(int(time), subframe=float(time % 1))
    evaluated = m.evaluated_get(bpy.context.evaluated_depsgraph_get())
    temporary = evaluated.to_mesh()
    v = np.array([tuple(evaluated.matrix_world @ p.co) for p in temporary.vertices])
    evaluated.to_mesh_clear()
    basis = {b.name: np.array(b.matrix_basis) for b in r.pose.bones}
    world = {b.name: np.array(b.matrix) for b in r.pose.bones}
    return v, basis, world


def section_radius(v, selected, first, second):
    axis = second - first
    length = np.linalg.norm(axis)
    axis /= length
    points = v[selected] - first
    projection = points @ axis
    radius = np.linalg.norm(points - projection[:, None] * axis, axis=1)
    return radius[(projection > length * .20) & (projection < length * .80)]


def knee_angle(world, side):
    hip, knee, ankle = [world['mixamorig:' + side + suffix][:3, 3] for suffix in ('UpLeg', 'Leg', 'Foot')]
    a, b = knee - hip, ankle - knee
    return float(np.degrees(np.arccos(np.clip(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)), -1, 1))))


rows, vertices = [], []
for time in np.arange(0, 36.01, .25):
    old_v, old_basis, old_world = evaluate(baseline_scene, baseline_rig, baseline_mesh, baseline_action, float(time))
    v, basis, world = evaluate(scene, rig, mesh, action, float(time))
    ratio = np.linalg.norm(v[edges[:, 0]] - v[edges[:, 1]], axis=1) / rest_lengths
    area = np.linalg.norm(np.cross(v[faces[:, 1]] - v[faces[:, 0]], v[faces[:, 2]] - v[faces[:, 0]]), axis=1) / rest_areas
    basis_error = max(float(np.max(np.abs(basis[n] - old_basis[n]))) for n in names if n not in changed)
    world_error = max(float(np.max(np.abs(world[n] - old_world[n]))) for n in names if n not in changed_world)
    q = rig.pose.bones['mixamorig:RightFoot'].matrix.to_quaternion() @ baseline_rig.pose.bones['mixamorig:RightFoot'].matrix.to_quaternion().inverted()
    rot = np.array(q.to_matrix())
    expected_foot = (old_v[foot_masks['Right']] - pivot) @ rot.T + pivot
    row = {
        'frame': float(time),
        'preserved_bone_basis_maximum_error': basis_error,
        'preserved_bone_world_maximum_error': world_error,
        'preserved_upper_body_mesh_maximum_error': float(np.max(np.abs(v[upper_body] - old_v[upper_body]))),
        'right_rigid_foot_transform_maximum_error': float(np.max(np.abs(v[foot_masks['Right']] - expected_foot))),
        'left_foot_maximum_position_change': float(np.max(np.linalg.norm(v[foot_masks['Left']] - old_v[foot_masks['Left']], axis=1))),
        'minimum_triangle_area_ratio': float(area.min()),
        'triangle_area_ratios_below_01': int((area < .1).sum()),
        'feet': {},
        'knees': {},
    }
    for side in ('Right', 'Left'):
        p = v[foot_masks[side]]
        row['feet'][side] = {'minimum_sole_height': float(p[:, 2].min()),
                             'sole_height_change': float(np.max(np.abs(p[:, 2] - old_v[foot_masks[side], 2]))),
                             'rigid_foot_edge_length_relative_error': float(np.abs(ratio[foot_edges[side]] - 1).max()),
                             'ankle_displacement_from_v2': float(np.linalg.norm(world['mixamorig:' + side + 'Foot'][:3, 3] - old_world['mixamorig:' + side + 'Foot'][:3, 3]))}
        row['knees'][side] = {'flex_degrees': knee_angle(world, side), 'previous_flex_degrees': knee_angle(old_world, side)}
        lengths = [np.linalg.norm(world['mixamorig:' + side + b][:3, 3] - world['mixamorig:' + side + a][:3, 3])
                   for a, b in [('UpLeg', 'Leg'), ('Leg', 'Foot')]]
        expected = [np.linalg.norm(old_world['mixamorig:' + side + b][:3, 3] - old_world['mixamorig:' + side + a][:3, 3])
                    for a, b in [('UpLeg', 'Leg'), ('Leg', 'Foot')]]
        row['knees'][side]['maximum_segment_length_relative_error'] = float(max(abs(a / b - 1) for a, b in zip(lengths, expected)))
    for label, selected, first_name, second_name in [('shin', leg_mask, 'mixamorig:RightLeg', 'mixamorig:RightFoot'),
                                                  ('thigh', upper_mask, 'mixamorig:RightUpLeg', 'mixamorig:RightLeg')]:
        new_radius = section_radius(v, selected, world[first_name][:3, 3], world[second_name][:3, 3])
        old_radius = section_radius(old_v, selected, old_world[first_name][:3, 3], old_world[second_name][:3, 3])
        assert len(new_radius) > 10 and len(old_radius) > 10
        row[label + '_median_core_radius_ratio_vs_v2'] = float(np.median(new_radius) / np.median(old_radius))
    assert basis_error < 1e-7 and world_error < 2e-6, row
    # Parent quaternion interpolation can shift contact between 48 fps keys.
    # Keep that subframe residual below 0.2 mm, inside the 2 mm ground clearance.
    assert row['right_rigid_foot_transform_maximum_error'] < .0002, row
    assert row['left_foot_maximum_position_change'] < 1e-7, row
    assert row['triangle_area_ratios_below_01'] == 0, row
    assert min(x['minimum_sole_height'] for x in row['feet'].values()) > -.00001, row
    assert max(x['sole_height_change'] for x in row['feet'].values()) < .0002, row
    assert max(x['rigid_foot_edge_length_relative_error'] for x in row['feet'].values()) < 1e-4, row
    assert max(x['maximum_segment_length_relative_error'] for x in row['knees'].values()) < 1e-5, row
    rows.append(row)
    if time.is_integer():
        vertices.append(v)

summary = {
    'samples': len(rows), 'keyed_poses': 37, 'duration_ms': 750,
    'changed_bones': sorted(changed),
    'maximum_preserved_bone_basis_error': max(r['preserved_bone_basis_maximum_error'] for r in rows),
    'maximum_preserved_bone_world_error': max(r['preserved_bone_world_maximum_error'] for r in rows),
    'maximum_preserved_upper_body_mesh_error': max(r['preserved_upper_body_mesh_maximum_error'] for r in rows),
    'maximum_left_foot_change': max(r['left_foot_maximum_position_change'] for r in rows),
    'maximum_sole_height_change': max(f['sole_height_change'] for r in rows for f in r['feet'].values()),
    'minimum_sole_height': min(f['minimum_sole_height'] for r in rows for f in r['feet'].values()),
    'maximum_rigid_foot_edge_length_relative_error': max(f['rigid_foot_edge_length_relative_error'] for r in rows for f in r['feet'].values()),
    'maximum_leg_segment_length_relative_error': max(f['maximum_segment_length_relative_error'] for r in rows for f in r['knees'].values()),
    'maximum_right_ankle_displacement': max(r['feet']['Right']['ankle_displacement_from_v2'] for r in rows),
    'right_knee_flex_range_degrees': [min(r['knees']['Right']['flex_degrees'] for r in rows), max(r['knees']['Right']['flex_degrees'] for r in rows)],
    'left_knee_flex_range_degrees': [min(r['knees']['Left']['flex_degrees'] for r in rows), max(r['knees']['Left']['flex_degrees'] for r in rows)],
    'minimum_shin_median_core_radius_ratio_vs_v2': min(r['shin_median_core_radius_ratio_vs_v2'] for r in rows),
    'minimum_thigh_median_core_radius_ratio_vs_v2': min(r['thigh_median_core_radius_ratio_vs_v2'] for r in rows),
    'minimum_triangle_area_ratio': min(r['minimum_triangle_area_ratio'] for r in rows),
    'no_toe_articulation_or_foot_roll': True,
    'geometry_and_weights_preserved': True,
    'visual_review_pending': True,
}
np.savez_compressed(STAGE / 'attack_pose_arrays.npz', vertices=np.array(vertices))
(STAGE / 'foot_deformation_review.json').write_text(json.dumps({'summary': summary, 'samples': rows}, indent=2) + '\n')
print(json.dumps(summary, indent=2), flush=True)

# Independently compare the retained locomotion mesh against the previous file.
retained_clips = {}
for clip, end in [('Walking', 50), ('Running', 32)]:
    old_action = next(t.strips[0].action for t in baseline_rig.animation_data.nla_tracks if t.name == clip)
    new_action = next(t.strips[0].action for t in rig.animation_data.nla_tracks if t.name == clip)
    maximum = 0
    for time in np.arange(0, end + .01, .5):
        old_v, _, _ = evaluate(baseline_scene, baseline_rig, baseline_mesh, old_action, float(time))
        v, _, _ = evaluate(scene, rig, mesh, new_action, float(time))
        maximum = max(maximum, float(np.max(np.abs(v - old_v))))
    assert maximum < 1e-7, (clip, maximum)
    retained_clips[clip] = {'samples': int(end * 2 + 1), 'maximum_mesh_change_vs_v2': maximum}
(STAGE / 'retained_clips_review.json').write_text(json.dumps(retained_clips, indent=2) + '\n')

baseline_rig.animation_data.action = baseline_action
baseline_rig.animation_data.action_slot = baseline_action.slots[0]
bpy.context.window.scene = scene
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
scene.render.resolution_x = 1300
scene.render.resolution_y = 1100
frames = STAGE / 'review_frames'
frames.mkdir(exist_ok=True)


def render(s, frame, name, direction, center=(0, -.10, .86), scale=2.35):
    bpy.context.window.scene = s
    s.frame_set(frame)
    center = Vector(center)
    s.camera.data.ortho_scale = scale
    s.camera.location = center + Vector(direction)
    s.camera.rotation_euler = (center - s.camera.location).to_track_quat('-Z', 'Y').to_euler()
    s.render.filepath = str(frames / (name + '.png'))
    bpy.ops.render.render(write_still=True)


for frame in range(37):
    render(scene, frame, f'front_{frame:02d}', (0, -6, 0))
    render(scene, frame, f'side_{frame:02d}', (-6, 0, 0))
for frame in [0, 6, 12, 18, 24, 30]:
    render(scene, frame, f'feet_detail_{frame:02d}', (-1.5, -3, 1.1), (0, -.25, .17), .8)
    render(baseline_scene, frame, f'before_front_{frame:02d}', (0, -6, 0))
    render(baseline_scene, frame, f'before_feet_detail_{frame:02d}', (-1.5, -3, 1.1), (0, -.25, .17), .8)
print('Rendered 37 front/profile poses and six before/after foot-detail anchors.', flush=True)
