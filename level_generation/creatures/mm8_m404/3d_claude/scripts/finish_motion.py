"""Clear inherited death intersections; retain the user-approved Mixamo attacks unchanged."""
from pathlib import Path
import math
import sys
import bpy
import numpy as np
from mathutils import Matrix, Vector, Quaternion

p = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(p / 'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/rig_mixamo_attack.blend'))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene
action = bpy.data.actions['Death']
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
frames = np.arange(round(float(action.frame_range[1]) * 4) + 1) / 4
source = []
for frame in frames:
    scene.frame_set(int(frame), subframe=float(frame % 1))
    source.append({'basis': {b.name: b.matrix_basis.copy() for b in rig.pose.bones},
                   'world': {b.name: armik.W(rig, b.name).copy() for b in rig.pose.bones}})
rig.animation_data.action = None


def smooth(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)


phis = np.arange(-60, 61, 2)
upper, fore, hand = [rig.data.bones['B_R_' + part] for part in ('UpperArm', 'Forearm', 'Hand')]
upper_axis = (upper.matrix_local.inverted() @ fore.head_local).normalized()
fore_axis = (fore.matrix_local.inverted() @ hand.head_local).normalized()
roots = [rig.data.bones[f'B_R_Finger{i}'].head_local for i in (0, 1, 2, 4)]
wrist_axis = (hand.matrix_local.to_3x3().inverted() @ (sum(roots, Vector()) / 4 - hand.head_local)).normalized()
hand_relative = fore.matrix_local.to_3x3().inverted() @ hand.matrix_local.to_3x3()
costs, targets = [], []
for frame, row in zip(frames, source):
    weight = smooth((frame / 30 - .1) / .15)
    chest = row['world']['B_Spine1'].to_3x3() @ rig.data.bones['B_Spine1'].matrix_local.to_3x3().inverted()
    target = row['world']['B_R_Hand'].translation + chest @ Vector((-.10, -.015, 0)) * weight
    hand_world = row['world']['B_R_Hand']
    neutral = row['world']['B_R_Forearm'].to_quaternion() @ hand_relative.to_quaternion()
    rotation = hand_world.to_quaternion().slerp(neutral, .08 * weight)
    tilt = -math.radians(30) * smooth((frame / 30 - .4) / .2)
    rotation = Quaternion((1, 0, 0), tilt) @ rotation
    row['world']['B_R_Hand'] = armik.rot_world(hand_world, rotation.to_matrix())
    targets.append(target)
    matrices = [row['world']['B_R_' + part] for part in ('UpperArm', 'Forearm', 'Hand')]
    neutral_upper = (row['world']['B_R_Clavicle'].to_3x3() @
                     rig.data.bones['B_R_Clavicle'].matrix_local.to_3x3().inverted() @ upper.matrix_local.to_3x3())
    values = []
    for phi in phis:
        f, _, reach, u, _, _ = armik.fitted(*matrices, target, float(phi) * weight)
        _, upper_roll = armik.split_swing_twist((neutral_upper.inverted() @ u).to_quaternion(), upper_axis)
        _, roll = armik.split_swing_twist((f.inverted() @ matrices[2].to_3x3() @
                                         hand_relative.inverted()).to_quaternion(), fore_axis)
        distal = f @ Quaternion(fore_axis, .6 * roll).to_matrix()
        neutral_fore = u @ upper.matrix_local.to_3x3().inverted() @ fore.matrix_local.to_3x3()
        _, fore_roll = armik.split_swing_twist((neutral_fore.inverted() @ distal).to_quaternion(), fore_axis)
        q = (hand_relative.inverted() @ distal.inverted() @ matrices[2].to_3x3()).to_quaternion()
        swing, wrist_roll = armik.split_swing_twist(q, wrist_axis)
        limits = [(abs(math.degrees(upper_roll)), 57), (abs(math.degrees(fore_roll)), 87),
                  (math.degrees(min(swing.angle, 2 * math.pi - swing.angle)), 57),
                  (abs(math.degrees(wrist_roll)), 42)]
        values.append(sum(max(0, value - limit) ** 2 * 100 for value, limit in limits) + float(phi) ** 2 * .01)
    costs.append(np.array(values))
acc = costs[0]
back = []
transition = (phis[:, None] - phis[None, :]) ** 2 * .5
for cost in costs[1:]:
    table = acc[:, None] + transition
    back.append(np.argmin(table, axis=0))
    acc = table.min(axis=0) + cost
index = int(np.argmin(acc))
path = [index]
for previous in reversed(back):
    index = int(previous[index])
    path.append(index)
path = phis[np.array(path[::-1])].astype(float)
path = np.convolve(np.pad(path, 4, mode='edge'), np.array([1, 2, 3, 4, 5, 4, 3, 2, 1]) / 25, mode='valid')
poses = []
for frame, row, target, phi in zip(frames, source, targets, path):
    for name, matrix in row['basis'].items():
        rig.pose.bones[name].matrix_basis = matrix
    bpy.context.view_layer.update()
    weight = smooth((frame / 30 - .1) / .15)
    chest = row['world']['B_Spine1'].to_3x3() @ rig.data.bones['B_Spine1'].matrix_local.to_3x3().inverted()
    for side in 'LR':
        hand_world = row['world'][f'B_{side}_Hand']
        if side == 'R':
            matrices = [row['world']['B_R_' + part] for part in ('UpperArm', 'Forearm', 'Hand')]
            _, pole, _, _, _, _ = armik.fitted(*matrices, target, float(phi) * weight)
            armik.solve(rig, side, target, pole=pole, hand_rot=hand_world.to_3x3())
        else:
            delta = chest @ Vector((.075, -.015, 0)) * weight
            armik.solve(rig, side, hand_world.translation + delta, hand_rot=hand_world.to_3x3())
            rest = (rig.data.bones['B_L_Forearm'].matrix_local.inverted() @
                    rig.data.bones['B_L_Hand'].matrix_local).to_quaternion()
            neutral = armik.W(rig, 'B_L_Forearm').to_quaternion() @ rest
            rotation = hand_world.to_quaternion().slerp(neutral, .2 * weight)
            armik.set_world(rig, 'B_L_Hand', armik.rot_world(armik.W(rig, 'B_L_Hand'), rotation.to_matrix()))
        for base, child, helper, share in [('Forearm', 'Hand', 'ForearmTwist', .6),
                                           ('UpperArm', 'Forearm', 'UpperArmTwist', -.5)]:
            parent = rig.data.bones[f'B_{side}_{base}']
            end = rig.data.bones[f'B_{side}_{child}']
            axis = (parent.matrix_local.inverted() @ end.head_local).normalized()
            if base == 'Forearm':
                rel = (rig.pose.bones[parent.name].matrix.inverted() @ rig.pose.bones[end.name].matrix).to_quaternion()
                rest = (parent.matrix_local.inverted() @ end.matrix_local).to_quaternion()
                delta = rel @ rest.inverted()
            else:
                delta = rig.pose.bones[parent.name].matrix_basis.to_quaternion()
            _, angle = armik.split_swing_twist(delta, axis)
            rig.pose.bones[f'B_{side}_{helper}'].rotation_quaternion = Quaternion(axis, share * angle)
    cloth = row['world']['B_Loincloth'].copy()
    pelvis = row['world']['B_Pelvis'].to_3x3() @ rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
    cloth.translation += pelvis @ Vector((0, -.003, 0)) * weight
    armik.set_world(rig, 'B_Loincloth', cloth)
    poses.append({name: (rig.pose.bones[name].rotation_quaternion.copy(), rig.pose.bones[name].location.copy())
                  for name in ['B_Loincloth'] + [f'B_{s}_{part}' for s in 'LR' for part in
                  ('UpperArm', 'Forearm', 'Hand', 'UpperArmTwist', 'ForearmTwist')]})
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
previous = {}
for frame, pose in zip(frames, poses):
    for name, (rotation, location) in pose.items():
        if name in previous and rotation.dot(previous[name]) < 0:
            rotation = -rotation
        bone = rig.pose.bones[name]
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_quaternion = rotation
        bone.keyframe_insert('rotation_quaternion', frame=float(frame))
        if name == 'B_Loincloth':
            bone.location = location
            bone.keyframe_insert('location', frame=float(frame))
        previous[name] = rotation.copy()
for layer in action.layers:
    for strip in layer.strips:
        for channelbag in strip.channelbags:
            for curve in channelbag.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = 'LINEAR'
rig.animation_data.action = bpy.data.actions['Dead']
rig.animation_data.action_slot = bpy.data.actions['Dead'].slots[0]
for frame in (0, float(bpy.data.actions['Dead'].frame_range[1])):
    for name, (rotation, location) in poses[-1].items():
        bone = rig.pose.bones[name]
        bone.rotation_quaternion = rotation
        bone.keyframe_insert('rotation_quaternion', frame=frame)
        if name == 'B_Loincloth':
            bone.location = location
            bone.keyframe_insert('location', frame=frame)
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(p / 'work/rig_finished_motion.blend'))
assert len(poses) == 169
print('FINISHED_DEATH: preserved release; global elbow plane; sword and apron clearance.', flush=True)
