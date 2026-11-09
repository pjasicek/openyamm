import bpy
import itertools
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_study')
scene = bpy.data.scenes['MM6_Demon_Attack_Study']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Attack_Study_Rig']
obj = scene.objects['Demon_Attack_Study_Mesh']
rig.hide_set(False)

def reset():
    for bone in rig.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()

def evaluate():
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    coordinates = np.array([tuple(vertex.co) for vertex in mesh.vertices])
    evaluated.to_mesh_clear()
    return coordinates

def rotate_about_head(bone, rotation):
    head = bone.head.copy()
    bone.matrix = Matrix.Translation(head) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-head) @ bone.matrix
    bpy.context.view_layer.update()

def render(name, direction):
    center = rig.pose.bones['mixamorig:RightHand'].head + Vector((-.06, -.035, -.12))
    camera = scene.camera
    camera.data.ortho_scale = .65
    camera.location = center + Vector(direction) * 2
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(stage / (name + '.png'))
    bpy.ops.render.render(write_still=True)

reset()
rest = evaluate()
weights = np.zeros((len(rest), len(obj.vertex_groups)))
for vertex in obj.data.vertices:
    for entry in vertex.groups:
        weights[vertex.index, entry.group] = entry.weight
faces = np.array([list(face.vertices) for face in obj.data.polygons])
edges = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
rest_lengths = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
render('probe_right_hand_rest_front', (0, -3, .1))
render('probe_right_hand_rest_side', (-3, -.3, .1))
rotations = {}
for digit in ('Index', 'Middle', 'Pinky'):
    one, two, three = [rig.pose.bones['mixamorig:RightHand' + digit + str(index)] for index in (1, 2, 3)]
    first = two.head - one.head
    second = three.head - two.head
    difference = second.rotation_difference(first)
    rotation = Quaternion((1, 0, 0, 0)).slerp(difference, .5)
    rotate_about_head(two, rotation)
    rotations[digit] = {'knuckle': two.name,
                       'straightening_degrees': math.degrees(rotation.angle),
                       'distal_claw_bones_unchanged_locally': True}
posed = evaluate()
edge_ratios = np.linalg.norm(posed[edges[:, 0]] - posed[edges[:, 1]], axis=1) / rest_lengths
report = {'test_only_not_final_native_hand_pose': True, 'knuckle_tests': rotations, 'digits': {}}
distal_masks = {}
for digit in ('Thumb', 'Index', 'Middle', 'Pinky'):
    end = 3 if digit == 'Thumb' else 4
    ids = [obj.vertex_groups['mixamorig:RightHand' + digit + str(index)].index for index in (end - 1, end)]
    mask = weights[:, ids].sum(1) > .95
    distal_masks[digit] = mask
    selected_edges = np.all(mask[edges], axis=1)
    report['digits'][digit] = {'distal_vertices': int(mask.sum()), 'distal_edges': int(selected_edges.sum()),
        'max_distal_edge_ratio': float(edge_ratios[selected_edges].max()) if selected_edges.any() else None,
        'min_distal_edge_ratio': float(edge_ratios[selected_edges].min()) if selected_edges.any() else None}
report['distal_surface_minimum_pair_distances'] = {}
for first, second in itertools.combinations(distal_masks, 2):
    if distal_masks[first].any() and distal_masks[second].any():
        report['distal_surface_minimum_pair_distances'][first + '__' + second] = {
            label: float(np.linalg.norm(vertices[distal_masks[first]][:, None, :]
                                        - vertices[distal_masks[second]][None, :, :], axis=2).min())
            for label, vertices in [('rest', rest), ('straightening_test', posed)]}
render('probe_right_hand_open_front', (0, -3, .1))
render('probe_right_hand_open_side', (-3, -.3, .1))
(stage / 'finger_control_study.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
reset()
rig.hide_set(True)
camera = scene.camera
center = Vector((0, -.03, .85))
camera.data.ortho_scale = 2.12
camera.location = center + Vector((0, -3, .2)) * 2
camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
