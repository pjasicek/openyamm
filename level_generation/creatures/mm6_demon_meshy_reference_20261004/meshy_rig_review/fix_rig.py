import bpy
import json
import numpy as np
from pathlib import Path

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_rig_review')
scene = bpy.data.scenes['MM6_Demon_Rig_Repair']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Rig_Review']
obj = scene.objects['Demon_Rigged_Review']
source = np.load(stage / 'source_arrays.npz')
audit = json.loads((stage / 'source.json').read_text())['audit']
coordinates = np.array([tuple(vertex.co) for vertex in obj.data.vertices])
expected = source['vertices'][:, [0, 2, 1]].copy()
expected[:, 1] *= -1
assert np.max(np.abs(coordinates - expected)) < 1e-6, {
    'max_coordinate_difference': float(np.max(np.abs(coordinates - expected))),
    'mesh_bounds': [coordinates.min(0).tolist(), coordinates.max(0).tolist()],
    'expected_bounds': [expected.min(0).tolist(), expected.max(0).tolist()],
    'mesh_first': coordinates[:3].tolist(), 'source_first': expected[:3].tolist()}
names = audit['joint_names']
groups = {name: obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name) for name in names}
all_ids = list(range(len(obj.data.vertices)))
for group in obj.vertex_groups:
    group.remove(all_ids)
for vertex_id, (indices, weights) in enumerate(zip(source['joints'], source['weights'])):
    for joint_id, weight in zip(indices, weights):
        if weight > 0:
            groups[names[int(joint_id)]].add([vertex_id], float(weight), 'REPLACE')

# The extra shoulder-spike bones are at the shoulders in bind space, but Meshy
# parented them to forearms. Their local animation is identity in both clips.
# Correct the hierarchy while retaining every bind-space bone matrix.
matrices_before = {bone.name: bone.matrix_local.copy() for bone in rig.data.bones}
for item in scene.objects:
    item.select_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
if rig.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT')
parent_repairs = []
for name, parent in [('Bone_041', 'mixamorig:LeftShoulder'), ('Bone_036', 'mixamorig:RightShoulder')]:
    bone = rig.data.edit_bones[name]
    previous_parent = next(item['parent'] for item in json.loads(
        (stage / 'blender_rig_audit.json').read_text())['bones'] if item['name'] == name)
    bone.use_connect = False
    bone.parent = rig.data.edit_bones[parent]
    parent_repairs.append({'bone': name, 'old_parent': previous_parent, 'new_parent': parent})
bpy.ops.object.mode_set(mode='OBJECT')
matrix_error = max(abs(before[row][column] - rig.data.bones[name].matrix_local[row][column])
                   for name, before in matrices_before.items()
                   for row in range(4) for column in range(4))
assert matrix_error < 1e-6, {'bind_matrix_maximum_error': matrix_error}

# This creature has stiff talons and a broad clawed foot. The humanoid preset's
# toe curl twists that forefoot. Attach it to the foot and retain ankle motion;
# keep the source toe bones and their channels for future independent toe work.
changed = set()
counts = {}
for side in ('Left', 'Right'):
    foot = groups['mixamorig:' + side + 'Foot']
    toe_ids = {groups['mixamorig:' + side + suffix].index for suffix in ('ToeBase', 'Toe_End')}
    count = 0
    for vertex in obj.data.vertices:
        weights = {entry.group: entry.weight for entry in vertex.groups}
        transferred = sum(weights.get(group_id, 0) for group_id in toe_ids)
        if transferred > 0:
            foot.add([vertex.index], weights.get(foot.index, 0) + transferred, 'REPLACE')
            for group_id in toe_ids:
                obj.vertex_groups[group_id].remove([vertex.index])
            changed.add(vertex.index)
            count += 1
    counts[side] = count
sums = [sum(entry.weight for entry in vertex.groups) for vertex in obj.data.vertices]
assert max(abs(value - 1) for value in sums) < 1e-6
assert np.array_equal(coordinates, np.array([tuple(vertex.co) for vertex in obj.data.vertices]))
report = {'parent_repairs': parent_repairs, 'bind_matrix_maximum_error': matrix_error,
          'toe_weight_transfer_to_foot_vertices': counts, 'total_weight_changed_vertices': len(changed),
          'weight_sum_range': [min(sums), max(sums)], 'geometry_coordinates_unchanged': True,
          'skeleton_names_and_count_preserved': len(rig.data.bones),
          'clips_preserved': audit['animations']}
(stage / 'rig_corrections.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
properties = bpy.ops.export_scene.gltf.get_rna_type().properties
print('glTF export controls:', json.dumps({prop.identifier: [item.identifier for item in prop.enum_items]
    if prop.type == 'ENUM' else prop.type for prop in properties
    if any(part in prop.identifier for part in ('animation_mode', 'all_influences', 'force_sampling',
                                               'nla_strips', 'current_frame', 'def_bones'))}))
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'rig_corrected_checkpoint.blend'), copy=True)
