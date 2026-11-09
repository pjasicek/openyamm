"""Screen the actual keyed wrist path and forearm section, including the rejected baseline."""
import bpy
import json
import numpy as np
from pathlib import Path
from mathutils import Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation_v2')
scene = bpy.data.scenes['MM6_Demon_Attack']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Attack_Rig']
obj = scene.objects['Demon_Attack_Mesh']
action = bpy.data.actions['Demon_Native_Attack_v2']
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
for track in rig.animation_data.nla_tracks:
    track.mute = True
source = np.load(stage / 'source_geometry.npz')
names = list(source['group_names'])
rest = source['vertices']
old = np.load(stage.parent / 'attack_animation/attack_pose_arrays.npz')
old_markers = json.loads((stage.parent / 'attack_animation/pose_markers.json').read_text())
old_names = list(old['bone_names'])
geometry = {}
for side in ('Right', 'Left'):
    lower = rig.data.bones['mixamorig:' + side + 'ForeArm']
    hand = rig.data.bones['mixamorig:' + side + 'Hand']
    elbow, wrist = np.array(lower.head_local), np.array(hand.head_local)
    delta = wrist - elbow
    axis = delta / np.linalg.norm(delta)
    t = (rest - elbow) @ delta / np.dot(delta, delta)
    radius = np.linalg.norm(rest - elbow - np.outer((rest - elbow) @ axis, axis), axis=1)
    core = ((source['weights'][:, names.index(lower.name)] > .8) & (t > .2) & (t < .8) & (radius > .015))
    bases = [rig.data.bones['mixamorig:' + side + 'Hand' + digit + '1'].head_local
             for digit in ('Index', 'Middle', 'Pinky', 'Ring')]
    geometry[side] = {'core': core, 'radius': radius, 'rest_long': sum(bases, Vector()) / 4 - hand.head_local}

def radius_statistics(vertices, elbow, wrist, side):
    axis = (wrist - elbow) / np.linalg.norm(wrist - elbow)
    radius = np.linalg.norm(vertices - elbow - np.outer((vertices - elbow) @ axis, axis), axis=1)
    g = geometry[side]
    ratios = radius[g['core']] / g['radius'][g['core']]
    return {'minimum': float(ratios.min()), 'median': float(np.median(ratios))}

rows = []
upper_basis_error = 0
upper_joint_error = 0
for time in np.arange(0, 36.01, .25):
    scene.frame_set(int(time), subframe=float(time % 1))
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = np.array([tuple(v.co) for v in mesh.vertices])
    evaluated.to_mesh_clear()
    row = {'frame': float(time), 'sides': {}}
    for side in ('Right', 'Left'):
        lower = rig.pose.bones['mixamorig:' + side + 'ForeArm']
        hand = rig.pose.bones['mixamorig:' + side + 'Hand']
        skin_rotation = hand.matrix.to_quaternion() @ hand.bone.matrix_local.to_quaternion().inverted()
        palm_long = skin_rotation @ geometry[side]['rest_long']
        row['sides'][side] = {
            'forearm_core_radius_ratio': radius_statistics(vertices, np.array(lower.head), np.array(hand.head), side),
            'wrist_bend_degrees': float(np.rad2deg(palm_long.angle(hand.head - lower.head))),
        }
        if time % 1 == 0:
            index = int(time)
            # The user's approved chains comprise the clavicle and upper arm, including the elbow center.
            for suffix in ('Shoulder', 'Arm'):
                name = 'mixamorig:' + side + suffix
                bone = rig.pose.bones[name]
                basis_error = np.abs(np.array(bone.matrix_basis) - old['basis'][index, old_names.index(name)]).max()
                upper_basis_error = max(upper_basis_error, float(basis_error))
            for suffix in ('Shoulder', 'Arm', 'ForeArm'):
                name = 'mixamorig:' + side + suffix
                joint_error = np.linalg.norm(np.array(rig.pose.bones[name].head) - np.array(old_markers[index][name]))
                upper_joint_error = max(upper_joint_error, float(joint_error))
    rows.append(row)

baseline = []
for frame, vertices in enumerate(old['vertices']):
    row = {'frame': frame, 'sides': {}}
    for side in ('Right', 'Left'):
        elbow = np.array(old_markers[frame]['mixamorig:' + side + 'ForeArm'])
        wrist = np.array(old_markers[frame]['mixamorig:' + side + 'Hand'])
        row['sides'][side] = radius_statistics(vertices, elbow, wrist, side)
    baseline.append(row)

summary = {
    'actual_keyed_subframe_samples': len(rows),
    'maximum_wrist_bend_degrees': max(r['sides'][s]['wrist_bend_degrees'] for r in rows for s in geometry),
    'minimum_forearm_core_radius_ratio': min(r['sides'][s]['forearm_core_radius_ratio']['minimum'] for r in rows for s in geometry),
    'lowest_pose_median_forearm_core_radius_ratio': min(r['sides'][s]['forearm_core_radius_ratio']['median'] for r in rows for s in geometry),
    'rejected_baseline_lowest_pose_median_radius_ratio': min(r['sides'][s]['median'] for r in baseline for s in geometry),
    'maximum_approved_clavicle_upper_arm_basis_element_change': upper_basis_error,
    'maximum_approved_shoulder_elbow_center_change': upper_joint_error,
    'core_definition': 'Original forearm weight > .8, middle 20–80% of elbow/wrist axis; excludes axis radii <= .015.',
    'scope': 'Radial section screening detects winding loss; it is not a full volumetric or intersection proof.',
}
(stage / 'hand_revision_review.json').write_text(json.dumps({
    'summary': summary, 'samples': rows, 'rejected_v1_baseline': baseline,
}, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert upper_basis_error < 1e-5 and upper_joint_error < 1e-5, 'Approved upper-arm motion changed'
assert summary['maximum_wrist_bend_degrees'] < 46, 'Unreviewed intermediate wrist overbend'
assert summary['minimum_forearm_core_radius_ratio'] > .85, 'Forearm section collapse'
assert summary['lowest_pose_median_forearm_core_radius_ratio'] > .97, 'Distributed forearm winding still collapses skin'
