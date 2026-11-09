"""Inspect controls in a disposable copied scene; never alter the accepted rig."""
import bpy
import itertools
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_study')
source_scene = bpy.data.scenes['MM6_Demon_Rig_Repair']
source_rig = source_scene.objects['Demon_Rig_Review']
source_obj = source_scene.objects['Demon_Rigged_Review']
scene = bpy.data.scenes.get('MM6_Demon_Attack_Study')
if scene is None:
    scene = bpy.data.scenes.new('MM6_Demon_Attack_Study')
    rig = source_rig.copy()
    rig.data = source_rig.data.copy()
    rig.name = 'Demon_Attack_Study_Rig'
    rig.animation_data_clear()
    obj = source_obj.copy()
    obj.data = source_obj.data.copy()
    obj.name = 'Demon_Attack_Study_Mesh'
    obj.animation_data_clear()
    obj.parent = rig
    for modifier in obj.modifiers:
        if modifier.type == 'ARMATURE':
            modifier.object = rig
    scene.collection.objects.link(rig)
    scene.collection.objects.link(obj)
    camera_data = bpy.data.cameras.new('DemonAttackStudyCamera')
    camera = bpy.data.objects.new('DemonAttackStudyCamera', camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
else:
    rig = scene.objects['Demon_Attack_Study_Rig']
    obj = scene.objects['Demon_Attack_Study_Mesh']
bpy.context.window.scene = scene
rig.hide_set(False)
obj.hide_set(False)
rig.hide_render = False
obj.hide_render = False
rig.data.pose_position = 'POSE'
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1200
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (.62, .66, .7)
scene.display.shading.show_shadows = False
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.world = bpy.data.worlds.new('DemonAttackStudyWorld') if scene.world is None else scene.world
scene.world.color = (.055, .065, .08)
camera = scene.camera
camera.data.type = 'ORTHO'

def reset():
    for bone in rig.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()

def evaluate():
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    coordinates = np.array([tuple(evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices])
    evaluated.to_mesh_clear()
    return coordinates

def rotate_world(name, axis, degrees):
    bone = rig.pose.bones[name]
    pivot = bone.head.copy()
    rotation = Quaternion(axis, math.radians(degrees)).to_matrix().to_4x4()
    bone.matrix = Matrix.Translation(pivot) @ rotation @ Matrix.Translation(-pivot) @ bone.matrix
    bpy.context.view_layer.update()

def render(name, center, direction, scale):
    center = Vector(center)
    camera.data.ortho_scale = scale
    camera.location = center + Vector(direction) * 2
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(stage / (name + '.png'))
    bpy.ops.render.render(write_still=True)

reset()
rest = evaluate()
groups = {group.name: group.index for group in obj.vertex_groups}
weight_matrix = np.zeros((len(rest), len(groups)))
for vertex in obj.data.vertices:
    for entry in vertex.groups:
        weight_matrix[vertex.index, entry.group] = entry.weight
report = {'coordinate_system': 'Blender Z-up, front=-Y, anatomical right=-X',
          'source_scene_preserved': source_scene.name, 'study_scene': scene.name,
          'bone_count': len(rig.data.bones), 'bones': [
              {'name': bone.name, 'parent': bone.parent.name if bone.parent else None,
               'head': list(bone.head_local), 'tail': list(bone.tail_local), 'length': bone.length,
               'weighted_vertices_over_001': int((weight_matrix[:, groups[bone.name]] > .001).sum())}
              for bone in rig.data.bones], 'arm_chain_lengths': {}, 'digit_rest_measurements': {}, 'probes': {}}
for side in ('Left', 'Right'):
    arm, forearm, hand = (rig.data.bones['mixamorig:' + side + suffix] for suffix in ('Arm', 'ForeArm', 'Hand'))
    report['arm_chain_lengths'][side] = {
        'shoulder_to_elbow': (forearm.head_local - arm.head_local).length,
        'elbow_to_wrist': (hand.head_local - forearm.head_local).length,
        'forearm_display_bone_length': forearm.length,
        'forearm_tail_to_hand_head_offset': (hand.head_local - forearm.tail_local).length,
    }
    digits = {}
    for digit in ('Thumb', 'Index', 'Middle', 'Pinky'):
        count = 3 if digit == 'Thumb' else 4
        names = ['mixamorig:' + side + 'Hand' + digit + str(index) for index in range(1, count + 1)]
        chain = [rig.data.bones[name] for name in names]
        terminal_ids = [groups[name] for name in names[-2:]]
        mask = weight_matrix[:, terminal_ids].sum(1) > .75
        digits[digit] = {
            'bones': names,
            'chain_length': sum((second.head_local - first.head_local).length
                                for first, second in zip(chain, chain[1:])) + chain[-1].length,
            'base': list(chain[0].head_local), 'display_tip': list(chain[-1].tail_local),
            'distal_surface_vertices': int(mask.sum()),
            'distal_surface_centroid': rest[mask].mean(0).tolist() if mask.any() else None,
        }
    report['digit_rest_measurements'][side] = {'digits': digits, 'tip_pair_distances': {
        first + '__' + second: (Vector(digits[first]['display_tip']) - Vector(digits[second]['display_tip'])).length
        for first, second in itertools.combinations(digits, 2)}}

upper_face = (rest[:, 2] > 1.565) & (rest[:, 2] < 1.61) & (np.abs(rest[:, 0]) < .055) & (rest[:, 1] < -.36)
upper_skull = rest[:, 2] > 1.61
chin = (rest[:, 2] > 1.46) & (rest[:, 2] < 1.52) & (np.abs(rest[:, 0]) < .075) & (rest[:, 1] < -.36)
belly = (rest[:, 2] > .94) & (rest[:, 2] < 1.125) & (rest[:, 1] < -.16)
render('probe_head_rest_front', (0, -.29, 1.55), (0, -3, .12), .53)
render('probe_head_rest_side', (0, -.29, 1.55), (3, -.2, .12), .53)
for degrees in (12, 24):
    reset()
    rotate_world('Bone_025', (1, 0, 0), degrees)
    posed = evaluate()
    displacement = np.linalg.norm(posed - rest, axis=1)
    report['probes']['candidate_jaw_' + str(degrees)] = {
        name: {'vertices': int(mask.sum()), 'maximum_displacement': float(displacement[mask].max()),
               'mean_displacement': float(displacement[mask].mean())}
        for name, mask in [('upper_face', upper_face), ('upper_skull', upper_skull), ('lower_chin', chin)]}
    render('probe_jaw_' + str(degrees) + '_front', (0, -.29, 1.55), (0, -3, .12), .53)
    render('probe_jaw_' + str(degrees) + '_side', (0, -.29, 1.55), (3, -.2, .12), .53)

reset()
rotate_world('Bone_020', (0, 0, 1), 10)
tail_posed = evaluate()
displacement = np.linalg.norm(tail_posed - rest, axis=1)
report['probes']['tail_base_10_degrees'] = {
    'belly_maximum_displacement': float(displacement[belly].max()),
    'belly_vertices_moving_over_002': int((displacement[belly] > .002).sum())}
render('probe_tail_base_10_front', (0, -.03, .85), (0, -3, .2), 2.12)
render('probe_tail_base_10_rear', (0, -.03, .85), (0, 3, .2), 2.12)
reset()
rotate_world('mixamorig:RightArm', (0, 1, 0), 40)
rotate_world('mixamorig:RightForeArm', (0, 1, 0), 60)
posed = evaluate()
report['probes']['right_arm_raise'] = {'pose_is_a_control_test_not_the_authored_attack': True,
    'maximum_shoulder_tip_displacement': float(np.linalg.norm(posed - rest, axis=1)[
        weight_matrix[:, groups['Bone_036']] > .999].max()),
    'elbow_position': list(rig.pose.bones['mixamorig:RightForeArm'].head),
    'wrist_position': list(rig.pose.bones['mixamorig:RightHand'].head)}
render('probe_arm_raise_front', (0, -.03, .85), (0, -3, .2), 2.25)
render('probe_arm_raise_side', (0, -.03, .85), (3, -.3, .2), 2.25)
reset()
render('study_rest_front', (0, -.03, .85), (0, -3, .2), 2.12)
(stage / 'rig_control_study.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value for key, value in report.items()
                  if key not in ('bones', 'digit_rest_measurements')}, indent=2))
rig.hide_set(True)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
        area.spaces.active.shading.type = 'SOLID'
