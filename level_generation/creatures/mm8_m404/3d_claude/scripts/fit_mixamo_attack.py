"""Fit the owned Mixamo downward slash over the warrior's calibrated guard and rigid two-hand grip."""
from pathlib import Path
import hashlib
import json
import math
import sys
import numpy as np
import bpy
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree
project = Path(__file__).resolve().parents[1]
repo = project.parents[3]
sys.path.insert(0, str(project / 'scripts'))
import armik
source_path = repo / 'anim_library/mixamo/Great Sword Slash (2).fbx'
bpy.ops.wm.open_mainfile(filepath=str(project / 'work/rig_motion.blend'))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene
scene.render.fps = 30
scene.render.fps_base = 1
standing = bpy.data.actions['Standing']

def set_action(action):
    rig.animation_data_create()
    rig.animation_data.action = action
    if action is not None and action.slots:
        rig.animation_data.action_slot = action.slots[0]

def smooth(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)
set_action(standing)
scene.frame_set(0)
home = {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}
home_world = {bone.name: armik.W(rig, bone.name).copy() for bone in rig.pose.bones}
grips = {side: json.loads((project / f'work/grip_pose_{side}.json').read_text()) for side in 'RL'}
centres = {side: Vector(grips[side]['handle_centre_hand_local']) for side in 'RL'}
axis_local = Vector(grips['R']['handle_axis_hand_local']).normalized()
guard_centre = home_world['B_R_Hand'] @ centres['R']
guard_rotation = home_world['B_R_Hand'].to_quaternion()
left_relative = guard_rotation.inverted() @ home_world['B_L_Hand'].to_quaternion()
before_objects, before_actions = (set(bpy.data.objects), set(bpy.data.actions))
bpy.ops.import_scene.fbx(filepath=str(source_path))
source = next((obj for obj in set(bpy.data.objects) - before_objects if obj.type == 'ARMATURE'))
source_action = source.animation_data.action
source_fps = scene.render.fps / scene.render.fps_base
first, last = source_action.frame_range
duration = (last - first) / source_fps
assert abs(duration - 38 / 30) < 1e-06
prefix = next((bone.name for bone in source.pose.bones if bone.name.endswith('Hips')))[:-4]
mapping = {'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2', 'B_Neck': 'Neck', 'B_Head': 'Head'}
for side, long_side in (('L', 'Left'), ('R', 'Right')):
    for target, origin in (('Clavicle', 'Shoulder'), ('UpperArm', 'Arm'), ('Forearm', 'ForeArm'), ('Hand', 'Hand')):
        mapping[f'B_{side}_{target}'] = long_side + origin

def source_world(name):
    return source.matrix_world @ source.pose.bones[prefix + name].matrix
scene.frame_set(int(first), subframe=first % 1)
bpy.context.view_layer.update()
source_home = (
    {name: (source.matrix_world @ source.data.bones[prefix + origin].matrix_local).copy() for name,
    origin in mapping.items()}
)
offsets = json.loads(scene['rig_offsets'])
source_frames = {name: Matrix(offsets[name]['R_src']) for name in mapping}
anatomy = json.loads((project / 'work/source_rest.json').read_text())
hand = source_world('RightHand')
source_grip_local = (
    hand.inverted() @ ((source_world('RightHandIndex2').translation + source_world('RightHandPinky2'
    ).translation) * 0.5)
)
source_grip_home = hand @ source_grip_local
# Map the actual grips because the source rigs use different hand frames.
source_hand_bases = {}
for side, long_side in (('R', 'Right'), ('L', 'Left')):
    hand_matrix = source_world(long_side + 'Hand')
    centre_world = (
        (source_world(long_side + 'HandIndex2').translation + source_world(long_side + 'HandPinky2').translation) * 0.5
    )
    centre_local = hand_matrix.inverted() @ centre_world
    common_axis = (
        (source_world('RightHandIndex2').translation - source_world('RightHandPinky2').translation).normalized()
    )
    local_axis = (hand_matrix.to_3x3().inverted() @ common_axis).normalized()
    forward = (centre_local - local_axis * centre_local.dot(local_axis)).normalized()
    source_basis = Matrix((local_axis, forward, local_axis.cross(forward))).transposed()
    target_axis = Vector(grips[side]['handle_axis_hand_local']).normalized()
    forward = (centres[side] - target_axis * centres[side].dot(target_axis)).normalized()
    target_basis = Matrix((target_axis, forward, target_axis.cross(forward))).transposed()
    source_hand_bases[side] = source_basis @ target_basis.transposed()
source_axis_local = (
    hand.to_3x3().inverted() @ (source_world('RightHandIndex2').translation - source_world('RightHandPinky2'
    ).translation).normalized()
)
source_across = source_world('LeftArm').translation - source_world('RightArm').translation
target_across = home_world['B_L_UpperArm'].translation - home_world['B_R_UpperArm'].translation
yaw = math.atan2(target_across.y, target_across.x) - math.atan2(source_across.y, source_across.x)
alignment = Matrix.Rotation(yaw, 3, 'Z')
source_length = (
    sum(((source_world(a).translation - source_world(b).translation).length for a, b in (('RightArm',
    'RightForeArm'), ('RightForeArm', 'RightHand'))))
)
target_length = (
    sum(((home_world[a].translation - home_world[b].translation).length for a, b in (('B_R_UpperArm', 'B_R_Forearm'
    ), ('B_R_Forearm', 'B_R_Hand'))))
)
length_ratio = target_length / source_length
samples = []
for index in range(round(duration * 120) + 1):
    seconds = index / 120
    frame = first + seconds * source_fps
    scene.frame_set(int(frame), subframe=frame % 1)
    source_rotations = {}
    for name, origin in mapping.items():
        delta = source_world(origin).to_3x3().normalized() @ source_home[name].to_3x3().normalized().inverted()
        source_rotations[name] = alignment @ delta @ alignment.inverted() @ source_frames[name]
    for side, long_side in (('L', 'Left'), ('R', 'Right')):
        upper_name, fore_name = (f'B_{side}_UpperArm', f'B_{side}_Forearm')
        upper_direction = (
            (alignment @ (source_world(long_side + 'ForeArm').translation - source_world(long_side + 'Arm'
            ).translation)).normalized()
        )
        fore_direction = (
            (alignment @ (source_world(long_side + 'Hand').translation - source_world(long_side + 'ForeArm'
            ).translation)).normalized()
        )
        upper_rotation = (
            Vector(anatomy[upper_name]['seg']).rotation_difference(upper_direction).to_matrix() @
            source_frames[upper_name]
        )
        hinge = (upper_rotation @ Vector((0, 0, -1))).normalized()
        normal = upper_direction.cross(fore_direction).normalized()
        roll = math.atan2(upper_direction.dot(hinge.cross(normal)), hinge.dot(normal))
        upper_rotation = Quaternion(upper_direction, roll).to_matrix() @ upper_rotation
        fore_rotation = upper_rotation @ source_frames[upper_name].inverted() @ source_frames[fore_name]
        fore_axis = (source_frames[fore_name].inverted() @ Vector(anatomy[fore_name]['seg'])).normalized()
        fore_rotation = (fore_rotation @ fore_axis).rotation_difference(fore_direction).to_matrix() @ fore_rotation
        source_rotations[upper_name] = upper_rotation
        source_rotations[fore_name] = fore_rotation
    for side, long_side in (('R', 'Right'), ('L', 'Left')):
        source_rotations[f'B_{side}_Hand'] = (
            alignment @ source_world(long_side + 'Hand').to_3x3().normalized() @ source_hand_bases[side]
        )
    centre = (
        guard_centre + alignment @ (source_world('RightHand') @ source_grip_local - source_grip_home) * length_ratio
    )
    source_axis = alignment @ source_world('RightHand').to_3x3().normalized() @ source_axis_local
    samples.append((seconds * 30, source_rotations, centre, source_axis.normalized()))
source_limits = {}
source_times = np.r_[np.arange(0, duration, 1 / 48), duration]
for group, names in (
    (('arms', ('LeftArm', 'LeftForeArm', 'RightArm', 'RightForeArm')), ('hands', ('LeftHand', 'RightHand')))
):
    maximum_step = maximum_acceleration = 0.0
    for name in names:
        matrices = []
        for seconds in source_times:
            frame = first + seconds * source_fps
            scene.frame_set(int(frame), subframe=frame % 1)
            matrices.append(np.array(source_world(name).to_3x3().normalized()))
        matrices = np.array(matrices)
        delta = matrices[1:] @ np.swapaxes(matrices[:-1], 1, 2)
        angle = np.arccos(np.clip((np.trace(delta, axis1=1, axis2=2) - 1) / 2, -1, 1))
        skew = (
            np.stack((delta[:, 2, 1] - delta[:, 1, 2], delta[:, 0, 2] - delta[:, 2, 0], delta[:, 1, 0] - delta[:,
            0, 1]), axis=1)
        )
        vectors = skew / (2 * np.sinc(angle / np.pi)[:, None])
        velocity = vectors / np.diff(source_times)[:, None]
        maximum_step = max(maximum_step, float(np.linalg.norm(vectors, axis=1).max() * 180 / np.pi))
        acceleration = (
            np.linalg.norm(np.diff(velocity, axis=0), axis=1) / ((np.diff(source_times)[1:] +
            np.diff(source_times)[:-1]) / 2)
        )
        maximum_acceleration = max(maximum_acceleration, float(acceleration.max() * 180 / np.pi))
    source_limits[group] = maximum_step
    source_limits[group + '_acceleration'] = maximum_acceleration
scene['attack_source_limits'] = json.dumps(source_limits)
for obj in set(bpy.data.objects) - before_objects:
    bpy.data.objects.remove(obj, do_unlink=True)
for action in set(bpy.data.actions) - before_actions:
    bpy.data.actions.remove(action)
set_action(None)
frames = []
for frame, rotations, centre, source_axis in samples:
    forward = rotations['B_Spine2'] @ home_world['B_Spine2'].to_3x3().inverted() @ Vector((0, -1, 0))
    yaw = math.atan2(forward.x, -forward.y)
    magnitude = abs(yaw)
    start = math.radians(30)
    span = math.radians(15)
    limited = magnitude if magnitude <= start else start + span * math.tanh((magnitude - start) / span)
    correction = Matrix.Rotation(math.copysign(limited, yaw) - yaw, 3, 'Z')
    rotations = {name: correction @ rotation for name, rotation in rotations.items()}
    source_axis = correction @ source_axis
    for name, matrix in home.items():
        rig.pose.bones[name].matrix_basis = matrix
    bpy.context.view_layer.update()
    weight = min(smooth(frame / 4.5), smooth((duration * 30 - frame) / 4.5))
    for name in mapping:
        rotation = home_world[name].to_quaternion() if name in ('B_Neck', 'B_Head') else rotations[name].to_quaternion()
        rotation = home_world[name].to_quaternion().slerp(rotation, weight)
        armik.set_world(rig, name, armik.rot_world(armik.W(rig, name), rotation.to_matrix()))
    raw_rotation = rotations['B_R_Hand'].to_quaternion()
    raw_rotation = (raw_rotation @ axis_local).rotation_difference(source_axis) @ raw_rotation
    rotation = guard_rotation.slerp(raw_rotation, weight)
    centre = armik.W(rig, 'B_R_Hand').translation + rotation @ centres['R']
    centre.y -= 0.04 * smooth((centre.z - 1.5) / 0.3) * weight
    lift = smooth((centre.z - 1.45) / 0.3) * weight
    head_rotation = Quaternion((1, 0, 0), -math.radians(18) * lift) @ home_world['B_Head'].to_quaternion()
    armik.set_world(rig, 'B_Head', armik.rot_world(armik.W(rig, 'B_Head'), head_rotation.to_matrix()))
    axis = rotation @ axis_local
    left_rotation = rotations['B_L_Hand'].to_quaternion()
    left_axis = Vector(grips['L']['handle_axis_hand_local']).normalized()
    left_rotation = (left_rotation @ left_axis).rotation_difference(source_axis) @ left_rotation
    left_rotation = home_world['B_L_Hand'].to_quaternion().slerp(left_rotation, weight)
    left_rotation = (left_rotation @ left_axis).rotation_difference(axis) @ left_rotation
    rotations = {'R': rotation.to_matrix(), 'L': left_rotation.to_matrix()}
    refs = (
        {side: [armik.W(rig, f'B_{side}_{part}').copy() for part in ('UpperArm', 'Forearm', 'Hand')] for side in 'RL'}
    )
    for _ in range(12):
        for side in 'RL':
            shoulder, elbow, wrist = [matrix.translation for matrix in refs[side]]
            offset = rotations[side] @ centres[side] + (axis * 0.15 if side == 'L' else Vector())
            reach = (elbow - shoulder).length + (wrist - elbow).length - 0.003
            distance = centre - offset - shoulder
            if distance.length > reach:
                centre -= distance.normalized() * (distance.length - reach)
    (
        frames.append({'frame': frame, 'snap': {b.name: b.matrix_basis.copy() for b in rig.pose.bones}, 'refs'
        : refs, 'rotation': rotations, 'centre': centre, 'axis': axis, 'world': {n: armik.W(rig,
        n).copy() for n in ('B_Spine1', 'B_Head', 'B_L_Clavicle', 'B_R_Clavicle')}})
    )
# Fit the whole clip together so elbow planes and hand roll do not flip.
phis = np.arange(-180, 180, 15)
rolls = np.arange(-180, 180, 15)
choices = [(float(phi), float(roll)) for phi in phis for roll in rolls]
paths = {}
body = bpy.data.objects['Body']
head_points = np.array([v.co[:] for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value == 7])
head_inverse = np.array(rig.data.bones['B_Head'].matrix_local.inverted())
head_points = (np.c_[head_points, np.ones(len(head_points))] @ head_inverse.T)[:, :3]
head_centre = (head_points.min(0) + head_points.max(0)) * 0.5
head_radii = (head_points.max(0) - head_points.min(0)) * 0.5 + 0.04
all_local = (
    (np.c_[np.array([v.co[:] for v in body.data.vertices]), np.ones(len(body.data.vertices))] @ head_inverse.T)[:, :3]
)
head_faces = (
    [list(face.vertices) for face in body.data.polygons if all((body.data.attributes['piece'
    ].data[i].value == 7 for i in face.vertices))]
)
head_tree = BVHTree.FromPolygons(all_local.tolist(), head_faces, all_triangles=False)
for side in 'RL':
    upper, fore, hand = [rig.data.bones[f'B_{side}_{part}'] for part in ('UpperArm', 'Forearm', 'Hand')]
    rest_relative = fore.matrix_local.to_3x3().inverted() @ hand.matrix_local.to_3x3()
    fore_axis = (fore.matrix_local.inverted() @ hand.head_local).normalized()
    upper_axis = (upper.matrix_local.inverted() @ fore.head_local).normalized()
    roots = [rig.data.bones[f'B_{side}_Finger{i}'].head_local for i in (0, 1, 2, 4)]
    wrist_axis = (hand.matrix_local.to_3x3().inverted() @ (sum(roots, Vector()) / 4 - hand.head_local)).normalized()
    tables = []
    joint_tables = []
    for entry in frames:
        mu, mf, mh = entry['refs'][side]
        target = entry['centre'] - (entry['axis'] * 0.15 if side == 'L' else Vector())
        clav = entry['world'][f'B_{side}_Clavicle'].to_3x3()
        neutral_upper = (
            clav @ rig.data.bones[f'B_{side}_Clavicle'].matrix_local.to_3x3().inverted() @ upper.matrix_local.to_3x3()
        )
        costs = np.empty((len(phis), len(rolls)))
        joints = np.empty((len(phis), len(rolls), 3, 4))
        for j, roll in enumerate(rolls):
            rotation = Quaternion(entry['axis'], math.radians(float(roll))).to_matrix() @ entry['rotation'][side]
            wrist = target - rotation @ centres[side]
            for i, phi in enumerate(phis):
                f, _, reach, u, elbow, actual = armik.fitted(mu, mf, mh, wrist, float(phi))
                delta = (f.inverted() @ rotation @ rest_relative.inverted()).to_quaternion()
                _, fore_roll = armik.split_swing_twist(delta, fore_axis)
                distal = f @ Quaternion(fore_axis, 0.6 * fore_roll).to_matrix()
                neutral_fore = u @ upper.matrix_local.to_3x3().inverted() @ fore.matrix_local.to_3x3()
                _, distal_roll = armik.split_swing_twist((neutral_fore.inverted() @ distal).to_quaternion(), fore_axis)
                relative = (rest_relative.inverted() @ distal.inverted() @ rotation).to_quaternion()
                swing, twist = armik.split_swing_twist(relative, wrist_axis)
                swing = math.degrees(min(swing.angle, 2 * math.pi - swing.angle))
                twist = abs(math.degrees(twist))
                _, upper_roll = armik.split_swing_twist((neutral_upper.inverted() @ u).to_quaternion(), upper_axis)
                upper_roll = abs(math.degrees(upper_roll))
                points = (
                    np.array(elbow)[None] + np.linspace(0.2, 1.03, 8)[:, None] * (np.array(actual) -
                    np.array(elbow))[None]
                )
                upper_points = (
                    np.array(mu.translation)[None] + np.linspace(0.3, 1, 7)[:, None] * (np.array(elbow) -
                    np.array(mu.translation))[None]
                )
                head = entry['world']['B_Head']
                local = (
                    (np.concatenate([upper_points, points]) - np.array(head.translation)) @
                    np.array(head.to_3x3()) - head_centre
                )
                head_cost = 0.0
                for k, point in enumerate(local + head_centre):
                    nearest, normal, _, distance = head_tree.find_nearest(Vector(point))
                    signed = distance if (Vector(point) - nearest).dot(normal) >= 0 else -distance
                    radius = 0.115 if k < len(upper_points) else 0.08
                    head_cost = max(head_cost, max(0, radius - signed))
                chest = entry['world']['B_Spine1']
                local = (points - np.array(chest.translation)) @ np.array(chest.to_3x3())
                local[:, 1] += 0.06
                torso_cost = max(0, 1 - np.linalg.norm(local / np.array([0.25, 0.31, 0.28]), axis=1).min())
                joints[i, j] = (
                    [list((neutral_upper.inverted() @ u).to_quaternion()), list((u.inverted() @
                    f).to_quaternion()), list((f.inverted() @ rotation).to_quaternion())]
                )
                costs[i, j] = swing + 0.35 * twist + 0.2 * upper_roll + 0.06 * abs(float(phi)) + 0.03 * abs(float(roll))
                costs[i, j] += 1500 * max(0, swing - 53) ** 2 + 1500 * max(0, twist - 40) ** 2
                costs[i, j] += (
                    1500 * max(0, upper_roll - 53) ** 2 + 1000 * max(0, abs(math.degrees(distal_roll)) - 82) ** 2
                )
                costs[i, j] += 1000000000.0 * max(0, abs(math.degrees(fore_roll)) - 145) ** 2
                costs[i, j] += (
                    1000000000000.0 * max(0, reach - 0.995) ** 2 + 10000000000.0 * head_cost ** 2 + 100000.0 *
                    torso_cost ** 2
                )
        if entry is frames[0] or entry is frames[-1]:
            costs[:] = 1000000000000.0
            costs[np.where(phis == 0)[0][0], np.where(rolls == 0)[0][0]] = 0
        tables.append(costs)
        joint_tables.append(joints.reshape(-1, 3, 4))
    acc = tables[0].ravel().copy()
    back = []
    for k, table in enumerate(tables[1:], 1):
        dots = np.abs(np.einsum('cbi,pbi->cpb', joint_tables[k], joint_tables[k - 1], optimize=True))
        angles = np.degrees(2 * np.arccos(np.clip(dots, 0, 1)))
        transition = 3 * np.sum(angles * angles, axis=2) + 10000.0 * np.maximum(0, angles.max(2) - 12) ** 2
        total = transition + acc[None, :]
        selected = total.argmin(1)
        acc = total[np.arange(len(selected)), selected] + table.ravel()
        back.append(selected)
    choice = int(acc.argmin())
    path = [np.unravel_index(choice, tables[0].shape)]
    for selected in reversed(back):
        choice = int(selected[choice])
        path.append(np.unravel_index(choice, tables[0].shape))
    path.reverse()
    controls = np.array([(phis[i], rolls[j]) for i, j in path], float)
    controls = np.degrees(np.unwrap(np.radians(controls), axis=0))
    kernel = np.exp(-0.5 * (np.arange(-12, 13) / 4) ** 2)
    kernel /= kernel.sum()
    for axis_index in range(2):
        controls[:, axis_index] = np.convolve(np.pad(controls[:, axis_index], 12, mode='edge'), kernel, mode='valid')
    for k, entry in enumerate(frames):
        controls[k] *= min(smooth(entry['frame'] / 3), smooth((duration * 30 - entry['frame']) / 3))
    controls[0] = 0
    controls[-1] = 0
    paths[side] = controls
    print('GLOBAL_GRIP', side, float(acc.min()), flush=True)
poses = []
max_gap = 0
max_swing = {side: 0 for side in 'RL'}
previous_twist = {}
for index, entry in enumerate(frames):
    frame = entry['frame']
    for name, matrix in entry['snap'].items():
        rig.pose.bones[name].matrix_basis = matrix
    bpy.context.view_layer.update()
    fitted_centre = entry['centre'].copy()
    for _ in range(12):
        for side in 'RL':
            phi, roll = paths[side][index]
            rotation = Quaternion(entry['axis'], math.radians(float(roll))).to_matrix() @ entry['rotation'][side]
            shoulder, elbow, wrist = [m.translation for m in entry['refs'][side]]
            reach = (elbow - shoulder).length + (wrist - elbow).length - 0.002
            offset = rotation @ centres[side] + (entry['axis'] * 0.15 if side == 'L' else Vector())
            distance = fitted_centre - offset - shoulder
            if distance.length > reach:
                fitted_centre -= distance.normalized() * (distance.length - reach)
    for side in 'RL':
        phi, roll = paths[side][index]
        rotation = Quaternion(entry['axis'], math.radians(float(roll))).to_matrix() @ entry['rotation'][side]
        target = fitted_centre - (entry['axis'] * 0.15 if side == 'L' else Vector())
        wrist = target - rotation @ centres[side]
        _, pole, _, _, _, _ = armik.fitted(*entry['refs'][side], wrist, float(phi))
        armik.solve(rig, side, wrist, pole=pole, hand_rot=rotation)
        max_gap = max(max_gap, (armik.W(rig, f'B_{side}_Hand') @ centres[side] - target).length)
        max_swing[side] = max(max_swing[side], armik.wrist_cost(rig, side, rotation)[0])
    for side in 'RL':
        for base, child, helper, share in (
            (('Forearm', 'Hand', 'ForearmTwist', 0.6), ('UpperArm', 'Forearm', 'UpperArmTwist', -0.5))
        ):
            parent = rig.data.bones[f'B_{side}_{base}']
            local_axis = (parent.matrix_local.inverted() @ rig.data.bones[f'B_{side}_{child}'].head_local).normalized()
            if base == 'Forearm':
                relative = (
                    (rig.pose.bones[parent.name].matrix.inverted() @
                    rig.pose.bones[f'B_{side}_{child}'].matrix).to_quaternion()
                )
                neutral = (
                    (parent.matrix_local.inverted() @ rig.data.bones[f'B_{side}_{child}'].matrix_local).to_quaternion()
                )
                delta = relative @ neutral.inverted()
            else:
                delta = rig.pose.bones[parent.name].matrix_basis.to_quaternion()
            _, angle = armik.split_swing_twist(delta, local_axis)
            key = side + base
            if key in previous_twist:
                angle = previous_twist[key] + (angle - previous_twist[key] + math.pi) % (2 * math.pi) - math.pi
            previous_twist[key] = angle
            rig.pose.bones[f'B_{side}_{helper}'].rotation_quaternion = Quaternion(local_axis, share * angle)
    poses.append((frame, {bone.name: bone.rotation_quaternion.copy() for bone in rig.pose.bones}))
for name in ('Attack', 'Attack2'):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    set_action(action)
    previous = {}
    for frame, pose in poses:
        for bone_name, rotation in pose.items():
            if bone_name in previous and rotation.dot(previous[bone_name]) < 0:
                rotation = -rotation
            bone = rig.pose.bones[bone_name]
            bone.rotation_mode = 'QUATERNION'
            bone.rotation_quaternion = rotation
            bone.keyframe_insert('rotation_quaternion', frame=frame)
            previous[bone_name] = rotation.copy()
    rig.pose.bones['B_Pelvis'].location = home['B_Pelvis'].translation
    rig.pose.bones['B_Pelvis'].keyframe_insert('location', frame=0)
    rig.pose.bones['B_Pelvis'].keyframe_insert('location', frame=duration * 30)
    action.use_frame_range = True
    action.frame_start, action.frame_end = (0, duration * 30)
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for curve in channelbag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
set_action(bpy.data.actions['Attack'])
times = np.r_[np.arange(0, duration, 1 / 48), duration]

def blade_trace():
    points = []
    directions = []
    edges = []
    for seconds in times:
        frame = seconds * 30
        scene.frame_set(int(frame), subframe=frame % 1)
        matrix = armik.W(rig, 'Socket_Sword')
        points.append(tuple(matrix @ Vector((0, 1.42, 0))))
        directions.append(tuple((matrix.to_3x3() @ Vector((0, 1, 0))).normalized()))
        edges.append(tuple((matrix.to_3x3() @ Vector((1, 0, 0))).normalized()))
    points = np.array(points)
    directions = np.array(directions)
    edges = np.array(edges)
    velocity = np.diff(points, axis=0) / np.diff(times)[:, None]
    speed = np.linalg.norm(velocity, axis=1)
    pointing = directions[:-1] + directions[1:]
    pointing /= np.linalg.norm(pointing, axis=1)[:, None]
    good = pointing @ np.array([0, -1, 0]) >= math.cos(math.radians(70))
    assert good.any(), 'Slash never points toward the target'
    impact = int(np.argmax(np.where(good, speed, -1)))
    return (impact, velocity, pointing, edges)
impact, velocity, directions, edges = blade_trace()
axis = Vector(directions[impact])
edge = Vector(edges[impact] + edges[impact + 1]).normalized()
lead = Vector(velocity[impact])
lead = (lead - axis * lead.dot(axis)).normalized()
blade_roll = math.atan2(axis.dot(edge.cross(lead)), edge.dot(lead))
if abs(blade_roll) > math.radians(5):
    for name in ('Attack', 'Attack2'):
        set_action(bpy.data.actions[name])
        for frame, _ in poses:
            weight = min(smooth(frame / 4.5), smooth((duration * 30 - frame) / 4.5))
            bone = rig.pose.bones['Socket_Sword']
            bone.rotation_mode = 'QUATERNION'
            bone.rotation_quaternion = Quaternion((0, 1, 0), blade_roll * weight)
            bone.keyframe_insert('rotation_quaternion', frame=frame)
    set_action(bpy.data.actions['Attack'])
    impact, velocity, directions, edges = blade_trace()
scene['attack_impact_seconds'] = float((times[impact] + times[impact + 1]) * 0.5)
scene['attack_source'] = 'Mixamo Great Sword Downward Slash'
set_action(None)
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
scene.render.fps = 30
report = (
    {'source': str(source_path.relative_to(repo)), 'source_sha256'
    : hashlib.sha256(source_path.read_bytes()).hexdigest(), 'duration_s': duration, 'impact_s'
    : float(scene['attack_impact_seconds']), 'source_rotation_limits': source_limits, 'blade_roll_deg'
    : math.degrees(blade_roll), 'max_grip_gap_m': max_gap, 'max_wrist_swing_deg': max_swing, 'adaptation'
    : 'Source upper-body motion over the calibrated native stance; rigid ' 'two-hand grip; 0.15 s guard blends.'}
)
(project / 'work/mixamo_attack.json').write_text(json.dumps(report, indent=2))
print('MIXAMO_ATTACK', report, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(project / 'work/rig_mixamo_attack.blend'))
assert max_gap < 0.005, 'Two-hand target is outside arm reach'
