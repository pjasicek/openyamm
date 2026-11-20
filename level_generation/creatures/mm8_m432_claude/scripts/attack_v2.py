"""Attack v2 (2026-10-18, user review of the reduction: the v1 arms crossed, the right upper arm entered the
pauldron, the left hand floated beside the hilt; "find some fitting 2 handed animation, like the lizardman warrior").

The Lizardman Warrior's user-approved two-handed downward slash (Mixamo Great Sword Slash (2); fitted there by
../../mm8_m404/3d_claude/scripts/fit_mixamo_attack.py and fit_mixamo_legs.py, read only) fitted to this rig the
same way: world-rotation copy onto the cloned source frames, a rigid two-hand grip (left hand on the handle below
the right, at its Standing spacing), elbow plane and hand roll chosen over the whole clip (head and torso
clearance, wrist limits), blade roll so the edge leads, then the source steps and pelvis weight transfer under the
fitted upper body. The clip is retimed so the measured blow lands on the bound impact (0.916667 s) inside the
unchanged 55-frame Attack: the wind-up plays 1.2x slower easing to real speed at the blow, the follow-through at
the source speed, then the held Standing frame 0. Every other clip is untouched.

Input work/rig_textured_fit.blend (unchanged); output work/rig_textured_fit_attack_v2.blend (old clip kept as
Attack_v1) and work/attack_v2/fit.json. Run: tools/run_creature_blender.sh --token T <this script>."""
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
repo = project.parents[2]
sys.path.insert(0, str(project / 'scripts'))
import armik_v2 as armik  # noqa: E402
import os  # noqa: E402

source_path = repo / 'anim_library/mixamo/Great Sword Slash (2).fbx'
bpy.ops.wm.open_mainfile(filepath=str(project / 'work/rig_textured_fit.blend'))
rig = bpy.data.objects['Rig']
body = bpy.data.objects['Body']
scene = bpy.context.scene
assert scene.render.fps == 30 and scene.render.fps_base == 1
IMPACT_S = 0.916666667          # actors.yml attack_melee/attack_ranged impact
CLIP_FRAMES = 55                # regression: Attack 55 / 30 s
UPPER_LIMIT = float(os.environ.get('ATTACK_V2_UPPER', '60'))
FORE_SOFT = float(os.environ.get('ATTACK_V2_FORE', '80'))
impact_time = impact_azimuth = None
BULGE = tuple(float(x) for x in os.environ.get('ATTACK_V2_BULGE', '-0.12,-0.08,0').split(','))  # world, mid-rise
ARM_BONES = [f'B_{s}_{p}' for s in 'RL' for p in ('Clavicle', 'UpperArm', 'Forearm', 'Hand')]
WINDUP_SLOW = 1.2               # playbook: wind-up within +-20 % of the source reads fine
TIP = Vector((0, 1.36, 0))      # Socket_Sword local blade tip (SwordMesh local y range -0.29 .. 1.36)
old = bpy.data.actions['Attack']
old.name = 'Attack_v1'
old.use_fake_user = True
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
grips = {side: json.loads((project / f'work/grip_pose{"" if side == "R" else "_L"}.json').read_text())
         for side in 'RL'}
centres = {side: Vector(grips[side]['handle_centre_hand_local']) for side in 'RL'}
axis_local = Vector(grips['R']['handle_axis_hand_local']).normalized()
guard_centre = home_world['B_R_Hand'] @ centres['R']
guard_rotation = home_world['B_R_Hand'].to_quaternion()
guard_axis = guard_rotation @ axis_local
# The left hand sits this far down the handle from the right one in Standing (0.115 m).
left_spacing = -((home_world['B_L_Hand'] @ centres['L']) - guard_centre).dot(guard_axis)
assert .08 < left_spacing < .16, left_spacing

# --- upper body: the m404 fit with this rig's grips, head and sword ---------------------------------------------
before_objects, before_actions = set(bpy.data.objects), set(bpy.data.actions)
bpy.ops.import_scene.fbx(filepath=str(source_path))
source = next(obj for obj in set(bpy.data.objects) - before_objects if obj.type == 'ARMATURE')
source_action = source.animation_data.action
source_fps = scene.render.fps / scene.render.fps_base
first, last = source_action.frame_range
duration = (last - first) / source_fps
assert abs(duration - 38 / 30) < 1e-06
prefix = next(bone.name for bone in source.pose.bones if bone.name.endswith('Hips'))[:-4]
mapping = {'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2', 'B_Neck': 'Neck', 'B_Head': 'Head'}
for side, long_side in (('L', 'Left'), ('R', 'Right')):
    for target, origin in (('Clavicle', 'Shoulder'), ('UpperArm', 'Arm'), ('Forearm', 'ForeArm'), ('Hand', 'Hand')):
        mapping[f'B_{side}_{target}'] = long_side + origin


def source_world(name):
    return source.matrix_world @ source.pose.bones[prefix + name].matrix


scene.frame_set(int(first), subframe=first % 1)
bpy.context.view_layer.update()
source_home = {name: (source.matrix_world @ source.data.bones[prefix + origin].matrix_local).copy()
               for name, origin in mapping.items()}
offsets = json.loads(scene['rig_offsets'])
source_frames = {name: Matrix(offsets[name]['R_src']) for name in mapping}
anatomy = json.loads((project / 'work/source_rest.json').read_text())
hand = source_world('RightHand')
source_grip_local = hand.inverted() @ ((source_world('RightHandIndex2').translation
                                        + source_world('RightHandPinky2').translation) * 0.5)
source_grip_home = hand @ source_grip_local
# Map the actual grips because the source rig uses different hand frames.
source_hand_bases = {}
for side, long_side in (('R', 'Right'), ('L', 'Left')):
    hand_matrix = source_world(long_side + 'Hand')
    centre_world = (source_world(long_side + 'HandIndex2').translation
                    + source_world(long_side + 'HandPinky2').translation) * 0.5
    centre_local = hand_matrix.inverted() @ centre_world
    common_axis = (source_world('RightHandIndex2').translation - source_world('RightHandPinky2').translation).normalized()
    local_axis = (hand_matrix.to_3x3().inverted() @ common_axis).normalized()
    forward = (centre_local - local_axis * centre_local.dot(local_axis)).normalized()
    source_basis = Matrix((local_axis, forward, local_axis.cross(forward))).transposed()
    target_axis = Vector(grips[side]['handle_axis_hand_local']).normalized()
    forward = (centres[side] - target_axis * centres[side].dot(target_axis)).normalized()
    target_basis = Matrix((target_axis, forward, target_axis.cross(forward))).transposed()
    source_hand_bases[side] = source_basis @ target_basis.transposed()
source_axis_local = (hand.to_3x3().inverted() @ (source_world('RightHandIndex2').translation
                                                 - source_world('RightHandPinky2').translation)).normalized()
source_across = source_world('LeftArm').translation - source_world('RightArm').translation
target_across = home_world['B_L_UpperArm'].translation - home_world['B_R_UpperArm'].translation
alignment = Matrix.Rotation(math.atan2(target_across.y, target_across.x)
                            - math.atan2(source_across.y, source_across.x), 3, 'Z')
source_length = sum((source_world(a).translation - source_world(b).translation).length
                    for a, b in (('RightArm', 'RightForeArm'), ('RightForeArm', 'RightHand')))
target_length = sum((home_world[a].translation - home_world[b].translation).length
                    for a, b in (('B_R_UpperArm', 'B_R_Forearm'), ('B_R_Forearm', 'B_R_Hand')))
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
        upper_name, fore_name = f'B_{side}_UpperArm', f'B_{side}_Forearm'
        upper_direction = (alignment @ (source_world(long_side + 'ForeArm').translation
                                        - source_world(long_side + 'Arm').translation)).normalized()
        fore_direction = (alignment @ (source_world(long_side + 'Hand').translation
                                       - source_world(long_side + 'ForeArm').translation)).normalized()
        upper_rotation = (Vector(anatomy[upper_name]['seg']).rotation_difference(upper_direction).to_matrix()
                          @ source_frames[upper_name])
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
        source_rotations[f'B_{side}_Hand'] = (alignment @ source_world(long_side + 'Hand').to_3x3().normalized()
                                              @ source_hand_bases[side])
    centre = guard_centre + alignment @ (source_world('RightHand') @ source_grip_local - source_grip_home) * length_ratio
    source_axis = alignment @ source_world('RightHand').to_3x3().normalized() @ source_axis_local
    samples.append((seconds * 30, source_rotations, centre, source_axis.normalized()))
leg_names = ('Hips', 'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot',
             'RightToeBase')
leg_samples = []
for index in range(round(duration * 120) + 1):
    frame = first + index / 120 * source_fps
    scene.frame_set(int(frame), subframe=frame % 1)
    leg_samples.append({name: source_world(name).copy() for name in leg_names})
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
    start, span = math.radians(30), math.radians(15)
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
    # Overhead: keep the hilt a little forward of the brow and look down along the blow (m404 rule, scaled to the
    # shoulder height: m404 1.50 m start, this body's shoulders are lower by the height ratio).
    shoulder = (home_world['B_R_UpperArm'].translation.z + home_world['B_L_UpperArm'].translation.z) * .5
    high = shoulder + .12
    centre.y -= 0.04 * smooth((centre.z - high) / 0.3) * weight
    lift = smooth((centre.z - (high - .05)) / 0.3) * weight
    head_rotation = Quaternion((1, 0, 0), -math.radians(18) * lift) @ home_world['B_Head'].to_quaternion()
    armik.set_world(rig, 'B_Head', armik.rot_world(armik.W(rig, 'B_Head'), head_rotation.to_matrix()))
    axis = rotation @ axis_local
    left_rotation = rotations['B_L_Hand'].to_quaternion()
    left_axis = Vector(grips['L']['handle_axis_hand_local']).normalized()
    left_rotation = (left_rotation @ left_axis).rotation_difference(source_axis) @ left_rotation
    left_rotation = home_world['B_L_Hand'].to_quaternion().slerp(left_rotation, weight)
    left_rotation = (left_rotation @ left_axis).rotation_difference(axis) @ left_rotation
    rotations = {'R': rotation.to_matrix(), 'L': left_rotation.to_matrix()}
    frames.append({'frame': frame, 'snap': {b.name: b.matrix_basis.copy() for b in rig.pose.bones},
                   'rotation': rotations, 'centre': centre, 'axis': axis, 'weight': weight,
                   'chest': armik.W(rig, 'B_Spine2').copy(),
                   'arms': {n: armik.W(rig, n).to_3x3().normalized() for n in ARM_BONES}})

# Wind-up re-path (round 2, user review: "the arms bend unnaturally", rubber-hose arms at 0.6 s). The source's low
# back-swing at the right turns the hands ~185 degrees against the upper arms. Instead the grip rises from the guard
# to the source's own top of the wind-up along the shortest turn in the chest frame (a raise at the right side, the
# native intent), with the arms blended between the same two poses, and joins the source there; the torso, head and
# legs keep the source's back-swing. REPATH=0 keeps the source path.
chest0 = home_world['B_Spine2']
centre_z = [entry['centre'].z for entry in frames]
top_index = int(np.argmax([z if entry['frame'] < 22 else -9 for z, entry in zip(centre_z, frames)]))
top = frames[top_index]
REPATH = os.environ.get('ATTACK_V2_REPATH', '1') == '1'
bulge_local = chest0.to_3x3().inverted() @ Vector(BULGE)


def to_local(chest, matrix3):
    return chest.to_3x3().normalized().inverted() @ matrix3


for index, entry in enumerate(frames):
    for name, matrix in entry['snap'].items():
        rig.pose.bones[name].matrix_basis = matrix
    bpy.context.view_layer.update()
    if REPATH and index < top_index:
        e = smooth(entry['frame'] / top['frame'])
        chest = entry['chest']
        a_c = chest0.inverted() @ guard_centre
        b_c = top['chest'].inverted() @ top['centre']
        centre = chest @ (a_c.lerp(b_c, e) + bulge_local * math.sin(math.pi * e))
        rotations = {}
        for side in 'RL':
            guard_hand = guard_rotation.to_matrix() if side == 'R' else home_world['B_L_Hand'].to_3x3().normalized()
            q0 = to_local(chest0, guard_hand).to_quaternion()
            q1 = to_local(top['chest'], top['rotation'][side]).to_quaternion()
            if q0.dot(q1) < 0:
                q1 = -q1
            rotations[side] = chest.to_3x3().normalized() @ q0.slerp(q1, e).to_matrix()
        axis = rotations['R'] @ axis_local
        left_axis = Vector(grips['L']['handle_axis_hand_local']).normalized()
        rotations['L'] = (rotations['L'] @ left_axis).rotation_difference(axis).to_matrix() @ rotations['L']
        # Arms between the guard and the top pose too, so the reference arms are not the twisted source arms.
        for name in ARM_BONES:
            q0 = to_local(chest0, home_world[name].to_3x3().normalized()).to_quaternion()
            q1 = to_local(top['chest'], top['arms'][name]).to_quaternion()
            if q0.dot(q1) < 0:
                q1 = -q1
            armik.set_world(rig, name, armik.rot_world(armik.W(rig, name),
                                                       chest.to_3x3().normalized() @ q0.slerp(q1, e).to_matrix()))
        lift = smooth((centre.z - (high - .05)) / 0.3)
        head_rotation = Quaternion((1, 0, 0), -math.radians(18) * lift) @ home_world['B_Head'].to_quaternion()
        armik.set_world(rig, 'B_Head', armik.rot_world(armik.W(rig, 'B_Head'), head_rotation.to_matrix()))
        entry.update(centre=centre, rotation=rotations, axis=axis,
                     snap={b.name: b.matrix_basis.copy() for b in rig.pose.bones})
    centre, rotations, axis = entry['centre'], entry['rotation'], entry['axis']
    refs = {side: [armik.W(rig, f'B_{side}_{part}').copy() for part in ('UpperArm', 'Forearm', 'Hand')]
            for side in 'RL'}
    for _ in range(12):
        for side in 'RL':
            shoulder_p, elbow, wrist = [matrix.translation for matrix in refs[side]]
            offset = rotations[side] @ centres[side] + (axis * left_spacing if side == 'L' else Vector())
            reach = (elbow - shoulder_p).length + (wrist - elbow).length - 0.003
            distance = centre - offset - shoulder_p
            if distance.length > reach:
                centre -= distance.normalized() * (distance.length - reach)
    entry.update(centre=centre, refs=refs,
                 world={n: armik.W(rig, n).copy() for n in ('B_Spine1', 'B_Head', 'B_L_Clavicle', 'B_R_Clavicle')})
print('REPATH', REPATH, 'top of the wind-up at source frame', top['frame'], 'grip height', round(top['centre'].z, 3),
      flush=True)
# Fit the whole clip together so elbow planes and hand roll do not flip.
phis = np.arange(-180, 180, 15)
rolls = np.arange(-180, 180, 15)
paths = {}
head_face = np.array([x.value for x in body.data.attributes['head'].data], bool)
head_vertices = sorted({i for f in body.data.polygons if head_face[f.index] for i in f.vertices})
head_inverse = np.array(rig.data.bones['B_Head'].matrix_local.inverted())
head_points = np.array([body.data.vertices[i].co[:] for i in head_vertices])
head_points = (np.c_[head_points, np.ones(len(head_points))] @ head_inverse.T)[:, :3]
head_centre = (head_points.min(0) + head_points.max(0)) * 0.5
# The head set is an open shell (neck cut): a nearest-face sign is meaningless far from it, so only points inside
# the head's own box (grown by the clearance radius) can count as penetration.
head_low, head_high = head_points.min(0) - 0.12, head_points.max(0) + 0.12
all_local = (np.c_[np.array([v.co[:] for v in body.data.vertices]), np.ones(len(body.data.vertices))]
             @ head_inverse.T)[:, :3]
head_faces = [list(face.vertices) for face in body.data.polygons if head_face[face.index]]
head_tree = BVHTree.FromPolygons(all_local.tolist(), head_faces, all_triangles=False)
for side in 'RL':
    upper, fore, hand_bone = [rig.data.bones[f'B_{side}_{part}'] for part in ('UpperArm', 'Forearm', 'Hand')]
    rest_relative = fore.matrix_local.to_3x3().inverted() @ hand_bone.matrix_local.to_3x3()
    fore_axis = (fore.matrix_local.inverted() @ hand_bone.head_local).normalized()
    upper_axis = (upper.matrix_local.inverted() @ fore.head_local).normalized()
    roots = [rig.data.bones[f'B_{side}_Finger{i}'].head_local for i in (0, 1, 2, 4)]
    wrist_axis = (hand_bone.matrix_local.to_3x3().inverted() @ (sum(roots, Vector()) / 4
                                                                - hand_bone.head_local)).normalized()
    tables = []
    joint_tables = []
    part_tables = []
    for entry in frames:
        armik.HINGE_BLEND = min(smooth(entry['frame'] / 4.5), smooth((duration * 30 - entry['frame']) / 4.5))
        mu, mf, mh = entry['refs'][side]
        target = entry['centre'] - (entry['axis'] * left_spacing if side == 'L' else Vector())
        clav = entry['world'][f'B_{side}_Clavicle'].to_3x3()
        neutral_upper = (clav @ rig.data.bones[f'B_{side}_Clavicle'].matrix_local.to_3x3().inverted()
                         @ upper.matrix_local.to_3x3())
        costs = np.empty((len(phis), len(rolls)))
        joints = np.empty((len(phis), len(rolls), 3, 4))
        parts = np.empty((len(phis), len(rolls), 8))
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
                points = np.array(elbow)[None] + np.linspace(0.2, 1.03, 8)[:, None] * (np.array(actual)
                                                                                      - np.array(elbow))[None]
                upper_points = np.array(mu.translation)[None] + np.linspace(0.3, 1, 7)[:, None] * (
                    np.array(elbow) - np.array(mu.translation))[None]
                head = entry['world']['B_Head']
                local = (np.concatenate([upper_points, points]) - np.array(head.translation)) @ np.array(
                    head.to_3x3()) - head_centre
                head_cost = 0.0
                for k, point in enumerate(local + head_centre):
                    if np.any(point < head_low) or np.any(point > head_high):
                        continue
                    nearest, normal, _, distance = head_tree.find_nearest(Vector(point))
                    signed = distance if (Vector(point) - nearest).dot(normal) >= 0 else -distance
                    radius = 0.115 if k < len(upper_points) else 0.08
                    head_cost = max(head_cost, max(0, radius - signed))
                chest = entry['world']['B_Spine1']
                local = (points - np.array(chest.translation)) @ np.array(chest.to_3x3())
                local[:, 1] += 0.06
                torso_cost = max(0, 1 - np.linalg.norm(local / np.array([0.25, 0.31, 0.28]), axis=1).min())
                joints[i, j] = [list((neutral_upper.inverted() @ u).to_quaternion()),
                                list((u.inverted() @ f).to_quaternion()), list((f.inverted() @ rotation).to_quaternion())]
                parts[i, j] = (swing, twist, upper_roll, abs(math.degrees(fore_roll)), abs(math.degrees(distal_roll)),
                               reach, head_cost, torso_cost)
                costs[i, j] = swing + 0.35 * twist + 0.2 * upper_roll + 0.06 * abs(float(phi)) + 0.03 * abs(float(roll))
                costs[i, j] += 1500 * max(0, swing - 53) ** 2 + 1500 * max(0, twist - 40) ** 2
                # The source wind-up needs ~185 degrees of hand roll against the upper arm on the right side; the
                # m404 limits (upper-arm roll 53) left it all to the forearm (137 deg, a visible candy wrap). Split it:
                # shoulder roll up to UPPER_LIMIT, forearm twist softly limited from FORE_SOFT.
                costs[i, j] += 1500 * max(0, upper_roll - UPPER_LIMIT) ** 2 + 1000 * max(0, abs(math.degrees(distal_roll)) - 82) ** 2
                costs[i, j] += 1500 * max(0, abs(math.degrees(fore_roll)) - FORE_SOFT) ** 2
                costs[i, j] += 1e9 * max(0, abs(math.degrees(fore_roll)) - 145) ** 2
                costs[i, j] += 1e12 * max(0, reach - 0.995) ** 2 + 1e10 * head_cost ** 2 + 1e5 * torso_cost ** 2
        if entry is frames[0] or entry is frames[-1]:
            costs[:] = 1e12
            costs[np.where(phis == 0)[0][0], np.where(rolls == 0)[0][0]] = 0
        tables.append(costs)
        joint_tables.append(joints.reshape(-1, 3, 4))
        part_tables.append(parts)
    acc = tables[0].ravel().copy()
    back = []
    for k, table in enumerate(tables[1:], 1):
        dots = np.abs(np.einsum('cbi,pbi->cpb', joint_tables[k], joint_tables[k - 1], optimize=True))
        angles = np.degrees(2 * np.arccos(np.clip(dots, 0, 1)))
        transition = 3 * np.sum(angles * angles, axis=2) + 1e4 * np.maximum(0, angles.max(2) - 12) ** 2
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
    chosen = np.array([part_tables[k][i, j] for k, (i, j) in enumerate(path)])
    chosen_cost = np.array([tables[k][i, j] for k, (i, j) in enumerate(path)])
    print('PATH', side, 'max swing twist upper_roll fore_roll distal_roll reach head torso',
          np.round(chosen.max(0), 3).tolist(), 'frames over 1e5:',
          [round(frames[k]['frame'], 2) for k in np.flatnonzero(chosen_cost > 1e5)][:40], flush=True)
    worst = int(chosen_cost.argmax())
    print('WORST', side, frames[worst]['frame'], np.round(chosen[worst], 3).tolist(), flush=True)
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
WRIST_LIMIT = 55.0      # visible wrist bend (forearm vs wrist -> finger roots); playbook gate 60


def visible_bend(side):
    fore, hand_matrix = armik.W(rig, f'B_{side}_Forearm'), armik.W(rig, f'B_{side}_Hand')
    roots = [armik.W(rig, f'B_{side}_Finger{i}').translation for i in (1, 2, 3, 4)]
    fore_direction = (hand_matrix.translation - fore.translation).normalized()
    hand_direction = (sum(roots, Vector()) / 4 - hand_matrix.translation).normalized()
    return math.degrees(fore_direction.angle(hand_direction)), hand_direction.cross(fore_direction)


def project_wrist(side):
    """This project's wrist metric (wrist_axis_probe.py): swing and twist of the hand against the forearm, relative
    to rest, about the forearm axis."""
    fb, hb = rig.data.bones[f'B_{side}_Forearm'], rig.data.bones[f'B_{side}_Hand']
    fr = rig.pose.bones[fb.name].matrix.to_3x3() @ fb.matrix_local.to_3x3().inverted()
    hr = rig.pose.bones[hb.name].matrix.to_3x3() @ hb.matrix_local.to_3x3().inverted()
    swing_q, twist = armik.split_swing_twist((fr.inverted() @ hr).to_quaternion(), (hb.head_local - fb.head_local).normalized())
    return math.degrees(min(swing_q.angle, 2 * math.pi - swing_q.angle)), abs(math.degrees(twist))


def pose_frame(index, entry, correction, previous_twist):
    """Solve both arms for one sample; `correction` turns the whole two-hand grip about the right grip centre."""
    armik.HINGE_BLEND = min(smooth(entry['frame'] / 4.5), smooth((duration * 30 - entry['frame']) / 4.5))
    for name, matrix in entry['snap'].items():
        rig.pose.bones[name].matrix_basis = matrix
    bpy.context.view_layer.update()
    axis = correction @ entry['axis']
    rotations = {side: correction @ Quaternion(entry['axis'], math.radians(float(paths[side][index][1]))).to_matrix()
                 @ entry['rotation'][side] for side in 'RL'}
    fitted_centre = entry['centre'].copy()
    for _ in range(12):
        for side in 'RL':
            shoulder_p, elbow, wrist = [m.translation for m in entry['refs'][side]]
            reach = (elbow - shoulder_p).length + (wrist - elbow).length - 0.002
            offset = rotations[side] @ centres[side] + (axis * left_spacing if side == 'L' else Vector())
            distance = fitted_centre - offset - shoulder_p
            if distance.length > reach:
                fitted_centre -= distance.normalized() * (distance.length - reach)
    gap, swing = 0.0, {}
    for side in 'RL':
        target = fitted_centre - (axis * left_spacing if side == 'L' else Vector())
        wrist = target - rotations[side] @ centres[side]
        _, pole, _, _, _, _ = armik.fitted(*entry['refs'][side], wrist, float(paths[side][index][0]))
        armik.solve(rig, side, wrist, pole=pole, hand_rot=rotations[side])
        gap = max(gap, (armik.W(rig, f'B_{side}_Hand') @ centres[side] - target).length)
        swing[side] = armik.wrist_cost(rig, side, rotations[side])[0]
    for side in 'RL':
        for base, child, helper, share in (('Forearm', 'Hand', 'ForearmTwist', 0.6),
                                           ('UpperArm', 'Forearm', 'UpperArmTwist', -0.5)):
            parent = rig.data.bones[f'B_{side}_{base}']
            local_axis = (parent.matrix_local.inverted() @ rig.data.bones[f'B_{side}_{child}'].head_local).normalized()
            if base == 'Forearm':
                relative = (rig.pose.bones[parent.name].matrix.inverted()
                            @ rig.pose.bones[f'B_{side}_{child}'].matrix).to_quaternion()
                neutral = (parent.matrix_local.inverted()
                           @ rig.data.bones[f'B_{side}_{child}'].matrix_local).to_quaternion()
                delta = relative @ neutral.inverted()
            else:
                delta = rig.pose.bones[parent.name].matrix_basis.to_quaternion()
            _, angle = armik.split_swing_twist(delta, local_axis)
            key = side + base
            if key in previous_twist:
                angle = previous_twist[key] + (angle - previous_twist[key] + math.pi) % (2 * math.pi) - math.pi
            previous_twist[key] = angle
            rig.pose.bones[f'B_{side}_{helper}'].rotation_quaternion = Quaternion(local_axis, share * angle)
    bpy.context.view_layer.update()
    return gap, swing


# Wrist relief: where the source's handle direction would bend the right wrist past the limit, turn the whole grip
# (sword and both hands) toward the forearm by the excess, smoothed over time, and re-solve (three rounds).
corrections = [Vector() for _ in frames]          # rotation vectors (world), applied as the grip turn
kernel = np.exp(-0.5 * (np.arange(-16, 17) / 6) ** 2)
kernel /= kernel.sum()
for round_index in range(4):
    excess = []
    previous_twist = {}
    for index, entry in enumerate(frames):
        vector = corrections[index]
        turn = Quaternion(vector.normalized(), vector.length).to_matrix() if vector.length > 1e-9 else Matrix.Identity(3)
        pose_frame(index, entry, turn, previous_twist)
        weight = min(smooth(entry['frame'] / 4.5), smooth((duration * 30 - entry['frame']) / 4.5))
        total = Vector()
        for side in 'RL':
            bend, normal = visible_bend(side)
            amount = math.radians(max(0.0, bend - WRIST_LIMIT)) * 1.1 * weight
            if normal.length > 1e-9:
                total += normal.normalized() * amount
        excess.append(total)
    worst = max(e.length for e in excess)
    print('WRIST_RELIEF round', round_index, 'max excess deg', round(math.degrees(worst) / 1.1, 2), flush=True)
    if round_index == 3 or worst < math.radians(.5):
        break
    stack = np.array([list(e) for e in excess])
    stack = np.stack([np.convolve(np.pad(stack[:, c], 16, mode='edge'), kernel, mode='valid') for c in range(3)], 1)
    corrections = [corrections[k] + Vector(stack[k]) * 1.6 for k in range(len(frames))]
upper_poses = []
max_gap = 0
max_swing = {side: 0 for side in 'RL'}
max_bend = {side: 0 for side in 'RL'}
project_swing = {side: 0 for side in 'RL'}
project_twist = {side: 0 for side in 'RL'}
grip_turn_deg = 0.0
previous_twist = {}
for index, entry in enumerate(frames):
    vector = corrections[index]
    turn = Quaternion(vector.normalized(), vector.length).to_matrix() if vector.length > 1e-9 else Matrix.Identity(3)
    grip_turn_deg = max(grip_turn_deg, math.degrees(vector.length))
    gap, swing = pose_frame(index, entry, turn, previous_twist)
    max_gap = max(max_gap, gap)
    for side in 'RL':
        max_swing[side] = max(max_swing[side], swing[side])
        max_bend[side] = max(max_bend[side], visible_bend(side)[0])
        sw, tw = project_wrist(side)
        project_swing[side] = max(project_swing[side], sw)
        project_twist[side] = max(project_twist[side], tw)
    upper_poses.append((entry['frame'], {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}))
assert max_gap < 0.005, ('Two-hand target is outside arm reach', max_gap)
print('WRIST', 'visible bend', max_bend, 'grip turn deg', round(grip_turn_deg, 1), flush=True)


def key_action(name, poses, frame_end):
    action = bpy.data.actions.get(name)
    if action:
        bpy.data.actions.remove(action)
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    set_action(action)
    previous = {}
    for frame, pose in poses:
        for bone_name, basis in pose.items():
            bone = rig.pose.bones[bone_name]
            bone.rotation_mode = 'QUATERNION'
            rotation = basis.to_quaternion()
            if bone_name in previous and rotation.dot(previous[bone_name]) < 0:
                rotation = -rotation
            bone.rotation_quaternion = rotation
            bone.keyframe_insert('rotation_quaternion', frame=frame)
            previous[bone_name] = rotation.copy()
            if bone_name == 'B_Pelvis':
                bone.location = basis.translation
                bone.keyframe_insert('location', frame=frame)
    action.use_frame_range = True
    action.frame_start, action.frame_end = 0, frame_end
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for curve in channelbag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    return action


source_frames_end = duration * 30
key_action('AttackV2_upper', upper_poses, source_frames_end)


def blade_trace(end_frame):
    times = np.r_[np.arange(0, end_frame / 30, 1 / 48), end_frame / 30]
    points, directions, edges = [], [], []
    for seconds in times:
        frame = seconds * 30
        scene.frame_set(int(frame), subframe=frame % 1)
        matrix = armik.W(rig, 'Socket_Sword')
        points.append(tuple(matrix @ TIP))
        directions.append(tuple((matrix.to_3x3() @ Vector((0, 1, 0))).normalized()))
        edges.append(tuple((matrix.to_3x3() @ Vector((1, 0, 0))).normalized()))
    points, directions, edges = np.array(points), np.array(directions), np.array(edges)
    velocity = np.diff(points, axis=0) / np.diff(times)[:, None]
    speed = np.linalg.norm(velocity, axis=1)
    pointing = directions[:-1] + directions[1:]
    pointing /= np.linalg.norm(pointing, axis=1)[:, None]
    # Contact (round 2: the fastest-tip rule put "impact" while the blade still pointed up-forward): on the
    # downswing (fast, tip falling) the moment the blade passes level while pointing ahead (within 45 degrees of the
    # facing), interpolated between samples.
    elevation = np.degrees(np.arcsin(np.clip(pointing[:, 2], -1, 1)))
    azimuth = np.degrees(np.arctan2(pointing[:, 0], -pointing[:, 1]))
    down = (speed > .4 * speed.max()) & (velocity[:, 2] < 0) & (np.abs(azimuth) < 45)
    crossing = [k for k in range(len(elevation) - 1) if down[k] and elevation[k] > 0 >= elevation[k + 1]]
    assert crossing, 'The cut never brings the blade level in front'
    impact = crossing[0]
    mid = (times[:-1] + times[1:]) / 2
    share = elevation[impact] / (elevation[impact] - elevation[impact + 1])
    global impact_time, impact_azimuth
    impact_time = float(mid[impact] + share * (mid[impact + 1] - mid[impact]))
    impact_azimuth = float(azimuth[impact])
    return impact, times, velocity, pointing, edges, points


impact, times, velocity, directions, edges, _ = blade_trace(source_frames_end)
axis = Vector(directions[impact])
edge = Vector(edges[impact] + edges[impact + 1]).normalized()
lead = Vector(velocity[impact])
lead = (lead - axis * lead.dot(axis)).normalized()
blade_roll = math.atan2(axis.dot(edge.cross(lead)), edge.dot(lead))
if abs(blade_roll) > math.radians(5):
    for frame, pose in upper_poses:
        weight = min(smooth(frame / 4.5), smooth((source_frames_end - frame) / 4.5))
        pose['Socket_Sword'] = home['Socket_Sword'] @ Quaternion((0, 1, 0), blade_roll * weight).to_matrix().to_4x4()
    key_action('AttackV2_upper', upper_poses, source_frames_end)

# --- lower body: source steps and pelvis weight transfer (m404 fit_mixamo_legs.py) -------------------------------
lower = ['B_Pelvis'] + [f'B_{side}_{part}' for side in 'LR' for part in ('Thigh', 'Calf', 'Foot', 'Toe0')]
approved = []
for frame, _ in upper_poses:
    scene.frame_set(int(frame), subframe=float(frame % 1))
    approved.append({'basis': {b.name: b.matrix_basis.copy() for b in rig.pose.bones},
                     'world': {b.name: armik.W(rig, b.name).copy() for b in rig.pose.bones}})
set_action(None)


def plane(hip, knee, ankle):
    direction = (ankle - hip).normalized()
    pole = knee - hip
    pole = (pole - direction * pole.dot(direction)).normalized()
    return Matrix((direction, pole, direction.cross(pole))).transposed()


initial = leg_samples[0]
across = initial['LeftUpLeg'].translation - initial['RightUpLeg'].translation
target_across = home_world['B_L_Thigh'].translation - home_world['B_R_Thigh'].translation
leg_alignment = Matrix.Rotation(math.atan2(target_across.y, target_across.x) - math.atan2(across.y, across.x), 3, 'Z')
leg_source_length = sum((initial[a].translation - initial[b].translation).length
                        for a, b in (('LeftUpLeg', 'LeftLeg'), ('LeftLeg', 'LeftFoot')))
leg_target_length = sum((home_world[a].translation - home_world[b].translation).length
                        for a, b in (('B_L_Thigh', 'B_L_Calf'), ('B_L_Calf', 'B_L_Foot')))
leg_scale = leg_target_length / leg_source_length
pole_maps, sole = {}, {}
for side, long_side in (('L', 'Left'), ('R', 'Right')):
    names = [f'B_{side}_{part}' for part in ('Thigh', 'Calf', 'Foot')]
    target_plane = plane(*(home_world[n].translation for n in names))
    source_plane = plane(*(initial[long_side + part].translation for part in ('UpLeg', 'Leg', 'Foot')))
    pole_maps[side] = target_plane @ source_plane.transposed()
    groups = {body.vertex_groups[f'B_{side}_{part}'].index for part in ('Foot', 'Toe0')}
    points = [v.co.copy() for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in groups) > .5]
    inverse = rig.data.bones[f'B_{side}_Foot'].matrix_local.inverted()
    sole[side] = [inverse @ point for point in points]
    assert len(sole[side]) > 20
full_poses = []
foot_paths = {s: [] for s in 'LR'}
pelvis_path = []
maximum_grip_error = 0
minimum_sole = 100
for (frame, _), old_pose, src in zip(upper_poses, approved, leg_samples):
    for name, matrix in old_pose['basis'].items():
        rig.pose.bones[name].matrix_basis = home[name] if name in lower else matrix
    bpy.context.view_layer.update()
    weight = min(smooth(frame / 4.5), smooth((source_frames_end - frame) / 4.5))
    lifts = {s: max(0, min(src[n].translation.z - initial[n].translation.z
                          for n in (s + 'Foot', s + 'ToeBase'))) * leg_scale * weight for s in ('Left', 'Right')}
    support_lift = min(lifts.values())
    root_delta = leg_alignment @ (src['Hips'].translation - initial['Hips'].translation) * leg_scale * weight
    root_delta.z -= support_lift
    pelvis = home_world['B_Pelvis'].copy()
    delta = leg_alignment @ (src['Hips'].to_3x3() @ initial['Hips'].to_3x3().inverted()) @ leg_alignment.inverted()
    rotation = Quaternion().slerp(delta.to_quaternion(), weight).to_matrix() @ pelvis.to_3x3()
    pelvis = Matrix.LocRotScale(pelvis.translation + root_delta, rotation.to_quaternion(), Vector((1, 1, 1)))
    armik.set_world(rig, 'B_Pelvis', pelvis)
    targets = {}
    for side, long_side in (('L', 'Left'), ('R', 'Right')):
        name = f'B_{side}_Foot'
        foot = long_side + 'Foot'
        delta = leg_alignment @ (src[foot].to_3x3() @ initial[foot].to_3x3().inverted()) @ leg_alignment.inverted()
        rotation = Quaternion().slerp(delta.to_quaternion(), weight).to_matrix() @ home_world[name].to_3x3()
        travel = leg_alignment @ (src[foot].translation - initial[foot].translation) * leg_scale * weight
        target = home_world[name].translation + travel
        lift = lifts[long_side] - support_lift
        home_low = min((home_world[name] @ point).z for point in sole[side])
        target.z = home_low + lift - min((rotation @ point).z for point in sole[side])
        source_plane = plane(*(src[long_side + part].translation for part in ('UpLeg', 'Leg', 'Foot')))
        pole = pole_maps[side] @ source_plane.col[1]
        home_pole = plane(*(home_world[f'B_{side}_{part}'].translation for part in ('Thigh', 'Calf', 'Foot'))).col[1]
        pole = home_pole.lerp(pole, weight).normalized()
        targets[side] = target, rotation, pole
    lower_by = 0
    for side, (target, _, _) in targets.items():
        hip, knee, ankle = [armik.W(rig, f'B_{side}_{part}').translation for part in ('Thigh', 'Calf', 'Foot')]
        length = ((knee - hip).length + (ankle - knee).length) * .998
        horizontal = (target.x - hip.x) ** 2 + (target.y - hip.y) ** 2
        assert horizontal < length * length, 'Source step exceeds this creature leg reach'
        lower_by = max(lower_by, hip.z - target.z - math.sqrt(length * length - horizontal))
    if lower_by > 0:
        pelvis.translation.z -= lower_by
        armik.set_world(rig, 'B_Pelvis', pelvis)
    for side, (target, rotation, pole) in targets.items():
        armik.solve_leg(rig, side, target, rotation, pole)
        matrix = armik.W(rig, f'B_{side}_Foot')
        minimum_sole = min(minimum_sole, min((matrix @ point).z for point in sole[side]))
        foot_paths[side].append(tuple(matrix.translation))
    # Toes stay at their Standing relation to the foot.
    for side in 'LR':
        rig.pose.bones[f'B_{side}_Toe0'].matrix_basis = home[f'B_{side}_Toe0']
    bpy.context.view_layer.update()
    # Keep the fitted torso, arms and grip in world orientation while the hips carry their position.
    for bone in rig.pose.bones:
        if bone.name not in lower:
            armik.set_world(rig, bone.name, armik.rot_world(armik.W(rig, bone.name),
                                                            old_pose['world'][bone.name].to_3x3()))
    before = old_pose['world']['B_R_Hand'].inverted() @ old_pose['world']['B_L_Hand']
    after = armik.W(rig, 'B_R_Hand').inverted() @ armik.W(rig, 'B_L_Hand')
    maximum_grip_error = max(maximum_grip_error, (before.translation - after.translation).length)
    pelvis_path.append(tuple(armik.W(rig, 'B_Pelvis').translation))
    full_poses.append((frame, {b.name: b.matrix_basis.copy() for b in rig.pose.bones}))
assert maximum_grip_error < .0001, maximum_grip_error
assert minimum_sole >= -.003, minimum_sole
key_action('AttackV2_source', full_poses, source_frames_end)
blade_trace(source_frames_end)
impact_source = impact_time * 30   # source frames

# --- retime into the bound 55-frame clip --------------------------------------------------------------------------
impact_out = IMPACT_S * 30
ease = 6.0                                       # frames over which the slowed wind-up eases to real speed


def rate(f):
    return 1 / WINDUP_SLOW + (1 - 1 / WINDUP_SLOW) * smooth((f - (impact_out - ease)) / ease) if f < impact_out else 1


def source_at(f, f0):
    if f <= f0:
        return 0.0
    xs = np.linspace(f0, f, max(2, int((f - f0) * 16) + 1))
    values = np.array([rate(x) for x in xs])
    return float(np.sum((values[1:] + values[:-1]) * 0.5 * np.diff(xs)))


WINDUP_SLOW = min(WINDUP_SLOW, (impact_out - 2) / impact_source)
lo, hi = -40.0, impact_out
for _ in range(60):
    mid = (lo + hi) / 2
    if source_at(impact_out, mid) > impact_source:
        lo = mid
    else:
        hi = mid
start_out = (lo + hi) / 2
assert start_out >= 0, ('Wind-up does not fit before the bound impact', start_out)
end_out = impact_out + (source_frames_end - impact_source)
assert end_out <= CLIP_FRAMES, ('Follow-through runs past the clip', end_out)
step_count = len(full_poses) - 1
out_poses = []
for k in range(CLIP_FRAMES * 4 + 1):
    f = k / 4
    s = source_at(f, start_out) if f <= impact_out else impact_source + (f - impact_out)
    s = max(0.0, min(source_frames_end, s))
    x = s / source_frames_end * step_count
    i0 = min(int(math.floor(x)), step_count - 1)
    t = x - i0
    a, b = full_poses[i0][1], full_poses[i0 + 1][1]
    pose = {}
    for name in a:
        qa, qb = a[name].to_quaternion(), b[name].to_quaternion()
        if qa.dot(qb) < 0:
            qb = -qb
        pose[name] = Matrix.LocRotScale(a[name].translation.lerp(b[name].translation, t), qa.slerp(qb, t),
                                        Vector((1, 1, 1)))
    out_poses.append((f, pose))
attack = key_action('Attack', out_poses, CLIP_FRAMES)
for name in ('AttackV2_upper', 'AttackV2_source'):
    bpy.data.actions.remove(bpy.data.actions[name])
blade_trace(CLIP_FRAMES)
impact_seconds = impact_time
assert abs(impact_seconds - IMPACT_S) <= 1 / 96, impact_seconds
# Start and end on Standing frame 0 (the engine crossfades only briefly).
home_deviation = {}
for f in (0, CLIP_FRAMES):
    scene.frame_set(f)
    worst = max(((bone.matrix_basis.to_quaternion().rotation_difference(home[bone.name].to_quaternion()).angle,
                  bone.name) for bone in rig.pose.bones))
    home_deviation[f] = (math.degrees(worst[0]), worst[1])
set_action(None)
for bone in rig.pose.bones:
    bone.matrix_basis = Matrix()
report = {
    'source': str(source_path.relative_to(repo)),
    'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
    'reference_fit': 'mm8_m404/3d_claude/scripts/fit_mixamo_attack.py + fit_mixamo_legs.py (user-approved slash)',
    'source_duration_s': duration, 'clip_s': CLIP_FRAMES / 30, 'left_hand_spacing_m': left_spacing,
    'source_impact_s': impact_source / 30, 'impact_s': impact_seconds, 'bound_impact_s': IMPACT_S,
    'impact_rule': 'blade passes level, pointing ahead, on the downswing', 'impact_blade_azimuth_deg': impact_azimuth,
    'repath': REPATH, 'windup_top_source_frame': top['frame'], 'upper_limit_deg': UPPER_LIMIT, 'fore_soft_deg': FORE_SOFT,
    'windup_slow': WINDUP_SLOW, 'source_start_s': start_out / 30, 'source_end_s': end_out / 30,
    'blade_roll_deg': math.degrees(blade_roll), 'max_grip_gap_m': max_gap, 'max_grip_change_legs_m': maximum_grip_error,
    'max_wrist_swing_deg': max_swing, 'max_visible_wrist_bend_deg': max_bend, 'max_grip_turn_deg': grip_turn_deg,
    'project_wrist_swing_deg': project_swing, 'project_wrist_twist_deg': project_twist, 'minimum_sole_z_m': minimum_sole, 'leg_scale': leg_scale,
    'foot_travel_xyz_m': {s: np.ptp(foot_paths[s], axis=0).tolist() for s in 'LR'},
    'pelvis_travel_xyz_m': np.ptp(pelvis_path, axis=0).tolist(),
    'max_deviation_from_standing_frame0_deg': {str(k): v for k, v in home_deviation.items()},
}
(project / 'work/attack_v2').mkdir(exist_ok=True)
(project / 'work/attack_v2/fit.json').write_text(json.dumps(report, indent=2))
scene['attack_v2'] = json.dumps(report)
bpy.ops.wm.save_as_mainfile(filepath=str(project / 'work/rig_textured_fit_attack_v2.blend'))
print('ATTACK_V2', json.dumps(report), flush=True)
