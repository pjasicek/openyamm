"""Release the sword during the fall and settle the free right hand beside the native visible corpse weapon."""
from pathlib import Path
import math
import json
import sys
import bpy
import numpy as np
from mathutils import Matrix, Vector, Quaternion
p = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(p / 'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/rig_textured.blend'))
rig, body, sword = bpy.data.objects['Rig'], bpy.data.objects['Body'], bpy.data.objects['SwordMesh']
scene = bpy.context.scene
action = bpy.data.actions['Death']
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
end = float(action.frame_range[1])
frames = np.arange(round(end * 4) + 1) / 4
rows = []
for frame in frames:
    scene.frame_set(int(frame), subframe=float(frame % 1))
    rows.append({'basis': {b.name: b.matrix_basis.copy() for b in rig.pose.bones},
                 'world': {b.name: armik.W(rig, b.name).copy() for b in rig.pose.bones}})
rig.animation_data.action = None
rest_socket = rig.matrix_world @ rig.data.bones['Socket_Sword'].matrix_local
prop = np.array([tuple(rest_socket.inverted() @ (sword.matrix_world @ v.co)) for v in sword.data.vertices])
upper, fore, hand = [rig.data.bones['B_R_' + part] for part in ('UpperArm', 'Forearm', 'Hand')]
upper_axis = (upper.matrix_local.inverted() @ fore.head_local).normalized()
fore_axis = (fore.matrix_local.inverted() @ hand.head_local).normalized()
hand_relative = fore.matrix_local.to_3x3().inverted() @ hand.matrix_local.to_3x3()
roots = [rig.data.bones[f'B_R_Finger{i}'].head_local for i in (0, 1, 2, 4)]
wrist_axis = (hand.matrix_local.to_3x3().inverted() @ (sum(roots, Vector()) / 4 - hand.head_local)).normalized()
release_s = .35


def smooth(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)


def right_and_back(row):
    deform = row['world']['B_Spine1'].to_3x3() @ rig.data.bones['B_Spine1'].matrix_local.to_3x3().inverted()
    right = deform @ Vector((-1, 0, 0))
    right.z = 0
    right.normalize()
    return right, Vector((right.y, -right.x, 0))


phis = np.arange(-180, 180, 4)
costs, rotations, targets = [], [], []
for frame, row in zip(frames, rows):
    weight = smooth((frame / 30 - release_s) / .65)
    matrices = [row['world']['B_R_' + part] for part in ('UpperArm', 'Forearm', 'Hand')]
    right, back = right_and_back(row)
    rest = matrices[0].translation + right * .52 + back * .1
    rest.z = .21
    length = (matrices[1].translation - matrices[0].translation).length + (matrices[2].translation - matrices[1].translation).length
    delta = rest - matrices[0].translation
    if delta.length > length * .99:
        rest = matrices[0].translation + delta.normalized() * length * .99
    target = matrices[2].translation.lerp(rest, weight)
    targets.append(target)
    neutral_upper = (row['world']['B_R_Clavicle'].to_3x3() @
                     rig.data.bones['B_R_Clavicle'].matrix_local.to_3x3().inverted() @ upper.matrix_local.to_3x3())
    values, quats = [], []
    for phi in phis:
        if weight == 0:
            u, f = matrices[0].to_3x3(), matrices[1].to_3x3()
            elbow = matrices[1].translation
        else:
            f, _, _, u, elbow, _ = armik.fitted(*matrices, target, float(phi))
        h = matrices[2].to_quaternion().slerp((f @ hand_relative).to_quaternion(), weight).to_matrix()
        _, roll = armik.split_swing_twist((f.inverted() @ h @ hand_relative.inverted()).to_quaternion(), fore_axis)
        distal = f @ Quaternion(fore_axis, .6 * roll).to_matrix()
        neutral_fore = u @ upper.matrix_local.to_3x3().inverted() @ fore.matrix_local.to_3x3()
        _, fore_roll = armik.split_swing_twist((neutral_fore.inverted() @ distal).to_quaternion(), fore_axis)
        _, upper_roll = armik.split_swing_twist((neutral_upper.inverted() @ u).to_quaternion(), upper_axis)
        swing, wrist_roll = armik.split_swing_twist((hand_relative.inverted() @ distal.inverted() @ h).to_quaternion(), wrist_axis)
        excess = [max(0, abs(math.degrees(upper_roll)) - 57), max(0, abs(math.degrees(fore_roll)) - 87),
                  max(0, math.degrees(min(swing.angle, 2 * math.pi - swing.angle)) - 57),
                  max(0, abs(math.degrees(wrist_roll)) - 42), max(0, .11 - elbow.z) * 1000]
        values.append(sum(value * value for value in excess) * 1000)
        quats.append([tuple(u.to_quaternion()), tuple(f.to_quaternion()), tuple(h.to_quaternion())])
    costs.append(np.array(values))
    rotations.append(np.array(quats))
acc, backtrack = costs[0], []
for index, cost in enumerate(costs[1:], 1):
    transition = sum(1 - np.clip(rotations[index - 1][:, j] @ rotations[index][:, j].T, -1, 1) ** 2
                     for j in range(3)) * 5000
    table = acc[:, None] + transition
    backtrack.append(np.argmin(table, axis=0))
    acc = table.min(axis=0) + cost
index = int(np.argmin(acc))
path = [index]
for previous in reversed(backtrack):
    index = int(previous[index])
    path.append(index)
path = phis[np.array(path[::-1])]
right, back = right_and_back(rows[-1])
goal = rows[-1]['world']['B_R_UpperArm'].translation + right * .9 + back * .15
release_matrix = None
poses, previous_twist = [], {}
minimum_weapon = 100
for frame, row, target, phi in zip(frames, rows, targets, path):
    for name, matrix in row['basis'].items():
        rig.pose.bones[name].matrix_basis = matrix
    bpy.context.view_layer.update()
    seconds = frame / 30
    weight = smooth((seconds - release_s) / .65)
    if weight > 0:
        matrices = [row['world']['B_R_' + part] for part in ('UpperArm', 'Forearm', 'Hand')]
        _, pole, _, _, _, _ = armik.fitted(*matrices, target, float(phi))
        armik.solve(rig, 'R', target, pole=pole, hand_rot=matrices[2].to_3x3())
        neutral = armik.W(rig, 'B_R_Forearm').to_quaternion() @ hand_relative.to_quaternion()
        rotation = matrices[2].to_quaternion().slerp(neutral, weight)
        armik.set_world(rig, 'B_R_Hand', armik.rot_world(armik.W(rig, 'B_R_Hand'), rotation.to_matrix()))
        for base, child, helper, share in [('Forearm', 'Hand', 'ForearmTwist', .6),
                                           ('UpperArm', 'Forearm', 'UpperArmTwist', -.5)]:
            parent, end_bone = rig.data.bones['B_R_' + base], rig.data.bones['B_R_' + child]
            axis = (parent.matrix_local.inverted() @ end_bone.head_local).normalized()
            if base == 'Forearm':
                rel = (rig.pose.bones[parent.name].matrix.inverted() @ rig.pose.bones[end_bone.name].matrix).to_quaternion()
                rest = (parent.matrix_local.inverted() @ end_bone.matrix_local).to_quaternion()
                delta = rel @ rest.inverted()
            else:
                delta = rig.pose.bones[parent.name].matrix_basis.to_quaternion()
            _, angle = armik.split_swing_twist(delta, axis)
            if base in previous_twist:
                angle = previous_twist[base] + (angle - previous_twist[base] + math.pi) % (2 * math.pi) - math.pi
            previous_twist[base] = angle
            rig.pose.bones['B_R_' + helper].rotation_quaternion = Quaternion(axis, share * angle)
        opening = smooth((seconds - release_s) / .12)
        for bone in rig.pose.bones:
            if bone.name.startswith('B_R_Finger'):
                bone.rotation_quaternion = row['basis'][bone.name].to_quaternion().slerp(Quaternion(), opening)
    if abs(seconds - release_s) < .0001:
        release_matrix = armik.W(rig, 'Socket_Sword').copy()
        arc_direction, _ = right_and_back(row)
        candidates = []
        for sign in (-1, 1):
            edge = right * sign
            rotation = Matrix((edge, back, edge.cross(back))).transposed().to_quaternion()
            candidates.append((abs(rotation.dot(release_matrix.to_quaternion())), rotation))
        goal_rotation = max(candidates, key=lambda item: item[0])[1]
        goal.z = .008 - float((prop @ np.array(goal_rotation.to_matrix()).T)[:, 2].min())
    if seconds > release_s:
        assert release_matrix is not None
        progress = max(0, min(1, (seconds - release_s) / .6))
        rotation = release_matrix.to_quaternion().slerp(goal_rotation, smooth(progress))
        position = release_matrix.translation.lerp(goal, smooth(progress))
        position += arc_direction * (1.2 * math.sin(math.pi * progress))
        position.z = release_matrix.translation.z * (1 - progress ** 2) + goal.z * progress ** 2
        lowest = float((prop @ np.array(rotation.to_matrix()).T)[:, 2].min() + position.z)
        position.z += max(0, .008 - lowest)
        matrix = Matrix.LocRotScale(position, rotation, Vector((1, 1, 1)))
        armik.set_world(rig, 'Socket_Sword', matrix)
    matrix = armik.W(rig, 'Socket_Sword')
    minimum_weapon = min(minimum_weapon, float((prop @ np.array(matrix.to_3x3()).T)[:, 2].min() + matrix.translation.z))
    names = ['Socket_Sword'] + [b.name for b in rig.pose.bones if b.name.startswith('B_R_Finger')]
    names += ['B_R_' + part for part in ('UpperArm', 'Forearm', 'Hand', 'UpperArmTwist', 'ForearmTwist')]
    poses.append({name: (rig.pose.bones[name].rotation_quaternion.copy(), rig.pose.bones[name].location.copy()) for name in names})
for label, samples in [('Death', list(zip(frames, poses))), ('Dead', [(0, poses[-1]), (4, poses[-1])])]:
    action = bpy.data.actions[label]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    paths = {f'pose.bones["{name}"].rotation_quaternion' for name in poses[-1]}
    paths.add('pose.bones["Socket_Sword"].location')
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for curve in list(channelbag.fcurves):
                    if curve.data_path in paths:
                        channelbag.fcurves.remove(curve)
    previous = {}
    for frame, pose in samples:
        for name, (rotation, location) in pose.items():
            if name in previous and rotation.dot(previous[name]) < 0:
                rotation = -rotation
            bone = rig.pose.bones[name]
            bone.rotation_quaternion = rotation
            bone.keyframe_insert('rotation_quaternion', frame=float(frame))
            if name == 'Socket_Sword':
                bone.location = location
                bone.keyframe_insert('location', frame=float(frame))
            previous[name] = rotation.copy()
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for curve in channelbag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
assert minimum_weapon >= .007
report = {'right_hand_release_s': release_s, 'minimum_sword_z_m': minimum_weapon,
          'native_observation': 'The native corpse keeps the sword visible beside the body.',
          'adaptation': 'Release the right hand during the fall; settle the visible blade on the floor.'}
(p / 'work/death_settle.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p / 'work/rig_delivery_animation.blend'))
print('DEATH_SETTLE', report, flush=True)
