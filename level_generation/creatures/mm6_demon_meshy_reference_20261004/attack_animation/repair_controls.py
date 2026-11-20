import bpy
import json
import heapq
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation')
scene = bpy.data.scenes['MM6_Demon_Attack']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Attack_Rig']
obj = scene.objects['Demon_Attack_Mesh']
if rig.animation_data:
    rig.animation_data.action = None
    for track in rig.animation_data.nla_tracks:
        track.mute = True
rig.hide_set(False)
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
data = np.load(stage / 'source_geometry.npz')
v, faces = data['vertices'], data['faces']
weights = data['weights'].copy()
names = list(data['group_names'])
ids = {name: names.index(name) for name in names}
labels = np.load(stage / 'component_labels.npy')
jaw = ids['Bone_025']
head = ids['mixamorig:Head']
# Remove the jaw's accidental whole-skull influence, keeping soft neck transitions initially.
weights[:, head] += weights[:, jaw]
weights[:, jaw] = 0
center_x = -.0036084
front = (v[:, 1] < -.300) & (v[:, 2] > 1.45) & (np.abs(v[:, 0] - center_x) < .095)
jaw_plane = 1.527 + .36 * (v[:, 1] + .390)
jaw_fraction = np.clip((jaw_plane - v[:, 2]) / .012 + .5, 0, 1) * front
head_membership = data['weights'][:, [ids['Bone_025'], ids['mixamorig:Head'], ids['mixamorig:Neck']]].sum(1) > .80
head_region = (((v[:, 2] > 1.545) & (v[:, 1] < -.265)) | (v[:, 2] > 1.605)) & head_membership
for index in np.flatnonzero(head_region | (jaw_fraction > 0)):
    weights[index] = 0
    weights[index, jaw] = jaw_fraction[index]
    weights[index, head] = 1 - jaw_fraction[index]
# Individual disconnected teeth were identified from their paired front/profile geometry.
lower_teeth = [3337, 3420, 3466, 3850, 4299, 4382, 4553, 4637]
upper_teeth = [3040, 3301, 3480, 3520, 3740, 3999, 4221, 4397, 4557, 4778]
lower_ids = np.flatnonzero(np.isin(labels, lower_teeth + [3618]))  # 3618: mouth-floor/tongue island
upper_ids = np.flatnonzero(np.isin(labels, upper_teeth))
weights[lower_ids] = 0
weights[lower_ids, jaw] = 1
weights[upper_ids] = 0
weights[upper_ids, head] = 1
tip_masks = {}
edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
adjacency = [[] for _ in v]
for first, second in edges:
    distance = float(np.linalg.norm(v[first] - v[second]))
    adjacency[first].append((int(second), distance))
    adjacency[second].append((int(first), distance))
for side in ('Right', 'Left'):
    digits = ('Index', 'Middle', 'Pinky', 'Ring')
    columns = {digit: [ids['mixamorig:' + side + 'Hand' + digit + str(i)] for i in range(1, 5)] for digit in digits}
    membership = data['weights'][:, sum(columns.values(), [])].sum(1)
    low = (membership > .60) & (v[:, 2] < .700)
    visited = set()
    clusters = []
    for first in np.flatnonzero(low):
        if int(first) in visited:
            continue
        component = []
        stack = [int(first)]
        visited.add(int(first))
        while stack:
            index = stack.pop()
            component.append(index)
            for neighbor, _ in adjacency[index]:
                if low[neighbor] and neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        if len(component) > 5:
            digit = max(digits, key=lambda d: data['weights'][component][:, columns[d]].sum())
            clusters.append((digit, component))
    assert len(clusters) == 4 and len({d for d, _ in clusters}) == 4
    # Geodesic labels follow physical fingers through ambiguous automatic cross-digit weights.
    domain = (membership > .40) & (v[:, 2] < .765)
    distance = np.full(len(v), np.inf)
    assigned = np.full(len(v), -1, dtype=int)
    queue = []
    for digit, component in clusters:
        label = digits.index(digit)
        for index in component:
            distance[index] = 0
            assigned[index] = label
            heapq.heappush(queue, (0, index, label))
    while queue:
        cost, index, label = heapq.heappop(queue)
        if cost > distance[index] + 1e-9:
            continue
        for neighbor, length in adjacency[index]:
            if domain[neighbor] and cost + length < distance[neighbor]:
                distance[neighbor] = cost + length
                assigned[neighbor] = label
                heapq.heappush(queue, (cost + length, neighbor, label))
    for index in np.flatnonzero((assigned >= 0) & (v[:, 2] < .735)):
        digit = digits[assigned[index]]
        own = data['weights'][index, columns[digit]].copy()
        if own.sum() < 1e-6:
            own[:] = 0
            own[1] = 1
        own /= own.sum()
        weights[index] = 0
        weights[index, columns[digit]] = own
    for digit, component in clusters:
        selected = np.array(component)
        weights[selected] = 0
        weights[selected, columns[digit][2]] = 1
        tip_masks[side + '_' + digit] = selected.tolist()
    thumb_columns = [ids['mixamorig:' + side + 'HandThumb' + str(i)] for i in range(1, 5)]
    thumb = np.flatnonzero((data['weights'][:, thumb_columns].sum(1) > .65) & (v[:, 2] < .830))
    weights[thumb] = 0
    weights[thumb, thumb_columns[2]] = 1
    tip_masks[side + '_Thumb'] = thumb.tolist()
for name in ('Bone_036', 'Bone_041'):
    selected = (data['weights'][:, ids[name]] > .60) & (v[:, 2] > 1.460)
    weights[selected] = 0
    weights[selected, ids[name]] = 1
changed = np.flatnonzero(np.max(np.abs(weights - data['weights']), axis=1) > 1e-8)
# Rebuild from the saved native import weights on resumes; this also clears earlier helper contributions.
all_ids = list(range(len(v)))
for group in obj.vertex_groups:
    group.remove(all_ids)
for index in range(len(v)):
    vertex = obj.data.vertices[int(index)]
    for group in np.flatnonzero(weights[index] > 1e-7):
        obj.vertex_groups[int(group)].add([int(index)], float(weights[index, group]), 'REPLACE')
assert np.max(np.abs(weights.sum(1) - 1)) < 1e-5
for item in scene.objects:
    item.select_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
bone = rig.data.edit_bones['Bone_025']
bone.use_connect = False
bone.head = (center_x, -.292, 1.548)
bone.tail = (center_x, -.409, 1.496)
bone.roll = 0
bpy.ops.object.mode_set(mode='OBJECT')
rig.hide_set(False)
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()

def evaluate():
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    result = np.array([tuple(vertex.co) for vertex in mesh.vertices])
    evaluated.to_mesh_clear()
    return result

rest = evaluate()
assert np.max(np.abs(rest - v)) < 1e-5
def render(name, center, direction, scale):
    camera = scene.camera
    center = Vector(center)
    camera.data.ortho_scale = scale
    camera.location = center + Vector(direction) * 2
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(stage / (name + '.png'))
    bpy.ops.render.render(write_still=True)

report = {'changed_weight_vertices': len(changed), 'geometry_changed': False,
          'jaw_hinge': [center_x, -.292, 1.548], 'lower_tooth_components': lower_teeth,
          'upper_tooth_components': upper_teeth, 'jaw_test': {}, 'tip_tests': {}}
render('jaw_repaired_rest_side', (0, -.29, 1.55), (3, -.2, .12), .53)
pb = rig.pose.bones['Bone_025']
pivot = pb.head.copy()
pb.matrix = Matrix.Translation(pivot) @ Quaternion((1, 0, 0), math.radians(18)).to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ pb.matrix
bpy.context.view_layer.update()
posed = evaluate()
upper_skull = (v[:, 2] > 1.61) & head_membership
upper_face = (v[:, 2] > 1.565) & (v[:, 2] < 1.61) & (np.abs(v[:, 0]) < .055) & (v[:, 1] < -.36)
for label, selected in [('upper_skull', np.flatnonzero(upper_skull)), ('upper_face', np.flatnonzero(upper_face)), ('upper_teeth', upper_ids), ('lower_teeth', lower_ids)]:
    report['jaw_test'][label] = {'vertices': len(selected), 'max_displacement': float(np.linalg.norm(posed[selected] - rest[selected], axis=1).max())}
assert report['jaw_test']['upper_face']['max_displacement'] < 1e-5
assert report['jaw_test']['upper_skull']['max_displacement'] < 1e-5
render('jaw_repaired_open_front', (0, -.29, 1.55), (0, -3, .12), .53)
render('jaw_repaired_open_side', (0, -.29, 1.55), (3, -.2, .12), .53)
pb.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
lengths = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
for side in ('Right', 'Left'):
    for digit in ('Index', 'Middle', 'Pinky', 'Ring'):
        one, two, three = [rig.pose.bones['mixamorig:' + side + 'Hand' + digit + str(i)] for i in (1, 2, 3)]
        rotation = (three.head - two.head).rotation_difference(two.head - one.head)
        pivot = two.head.copy()
        two.matrix = Matrix.Translation(pivot) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ two.matrix
        bpy.context.view_layer.update()
posed = evaluate()
ratio = np.linalg.norm(posed[edges[:, 0]] - posed[edges[:, 1]], axis=1) / lengths
for label, selected in tip_masks.items():
    mask = np.zeros(len(v), dtype=bool)
    mask[selected] = True
    es = np.all(mask[edges], axis=1)
    report['tip_tests'][label] = {'vertices': len(selected), 'edges': int(es.sum()),
                                 'max_edge_error': float(np.max(np.abs(ratio[es] - 1))) if es.any() else None}
    if es.any():
        assert report['tip_tests'][label]['max_edge_error'] < .001
render('claws_repaired_open', (-.70, -.42, .72), (0, -3, .15), .66)
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
(stage / 'tip_vertex_masks.json').write_text(json.dumps(tip_masks, indent=2) + '\n')
np.savez_compressed(stage / 'repaired_weights.npz', weights=weights, jaw_vertex_ids=np.flatnonzero(weights[:, jaw] > .001), upper_teeth=upper_ids, lower_teeth=lower_ids)
(stage / 'control_repairs.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.data.libraries.write(str(stage / 'rig_repaired_checkpoint.blend'), {scene}, path_remap='RELATIVE')
print(json.dumps(report, indent=2))
