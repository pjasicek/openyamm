"""Native attack posing helpers. All transforms operate in armature space (identity object transform)."""
import bpy
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

STAGE = Path(__file__).resolve().parent
SPEC = json.loads((STAGE.parent / 'attack_study/attack_motion_spec.json').read_text())
SOURCE = np.load(STAGE / 'source_geometry.npz')
TIP_MASKS = json.loads((STAGE / 'tip_vertex_masks.json').read_text())
PIXEL_SCALE = .00650
TWIST_HISTORY = {}


def objects():
    scene = bpy.data.scenes['MM6_Demon_Attack']
    bpy.context.window.scene = scene
    return scene, scene.objects['Demon_Attack_Rig'], scene.objects['Demon_Attack_Mesh']


def update():
    bpy.context.view_layer.update()


def rotate(bone, quaternion):
    pivot = bone.head.copy()
    bone.matrix = Matrix.Translation(pivot) @ quaternion.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ bone.matrix
    update()


def direction_vector(points, start, end, length):
    dx = (points[end][0] - points[start][0]) * PIXEL_SCALE
    dz = (points[start][1] - points[end][1]) * PIXEL_SCALE
    projected = math.hypot(dx, dz)
    if projected > length * .985:
        dx *= length * .985 / projected
        dz *= length * .985 / projected
    dy = -math.sqrt(max(0, length * length - dx * dx - dz * dz))
    return Vector((dx, dy, dz))


def interpolate_vector(first, second, fraction):
    return (first * (1 - fraction) + second * fraction).normalized()


def palm_basis(direction, normal):
    direction = direction.normalized()
    normal = (normal - direction * direction.dot(normal)).normalized()
    width = direction.cross(normal).normalized()
    return Matrix((width, direction, normal)).transposed()


def hand_anchor(side, source, hand, rest_basis, lower_length):
    key = side.lower()
    points = source[key]
    desired_long = Vector(((points[3][0] - points[2][0]) * PIXEL_SCALE, -.065,
                           (points[2][1] - points[3][1]) * PIXEL_SCALE)).normalized()
    lower_direction = direction_vector(points, 1, 2, lower_length).normalized()
    bend = lower_direction.rotation_difference(desired_long)
    if bend.angle > math.radians(45):
        desired_long = Quaternion().slerp(bend, math.radians(45) / bend.angle) @ lower_direction
    frontal = source['inferred_control_seeds']['right_palm_front_facing_weight'] if side == 'Right' else .40
    inward = .90 * (1 - frontal) + .35 * frontal
    sign = 1 if side == 'Right' else -1
    normal_y = -.25 - frontal * .75 if side == 'Right' else (.75 if source['letter'] == 'c' else -.40)
    if side == 'Right' and source['letter'] == 'e':
        # The across-body stroke presents the claw's back/edge. Keeping a front-facing
        # palm through this reversal would demand a near half-turn of the forearm.
        normal_y = .75
    basis = palm_basis(desired_long, Vector((inward * sign, normal_y, 0)))
    return (basis @ rest_basis.transposed() @ hand.bone.matrix_local.to_3x3()).to_quaternion()


def assign(bone, quaternion, point):
    matrix = quaternion.to_matrix().to_4x4()
    matrix.translation = point
    bone.matrix = matrix
    update()


def solve_leg(rig, side, target):
    upper, lower, foot = [rig.pose.bones['mixamorig:' + side + suffix] for suffix in ('UpLeg', 'Leg', 'Foot')]
    upper_rest, lower_rest, foot_rest = [bone.bone.matrix_local for bone in (upper, lower, foot)]
    a = lower_rest.translation - upper_rest.translation
    b = foot_rest.translation - lower_rest.translation
    l1, l2 = a.length, b.length
    hip = upper.head.copy()
    delta = target - hip
    distance = delta.length
    assert abs(l1 - l2) < distance < l1 + l2, (side, distance, l1 + l2)
    axis = delta.normalized()
    forward = Vector((0, -1, 0))
    pole = (forward - axis * forward.dot(axis)).normalized()
    along = (l1 * l1 - l2 * l2 + distance * distance) / (2 * distance)
    knee = hip + axis * along + pole * math.sqrt(max(0, l1 * l1 - along * along))
    assign(upper, a.rotation_difference(knee - hip) @ upper_rest.to_quaternion(), hip)
    assign(lower, b.rotation_difference(target - knee) @ lower_rest.to_quaternion(), knee)
    assign(foot, foot_rest.to_quaternion(), target)


def pose_at(time_frame):
    scene, rig, mesh = objects()
    for bone in rig.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    update()
    segment = min(int(time_frame // 6), 5)
    following = min(segment + 1, 5)
    u = min(1, max(0, (time_frame - segment * 6) / 6))
    # Smooth secondary controls; main limb directions stay continuous through the source anchors.
    ease = u * u * (3 - 2 * u)
    a, b = SPEC['anchors'][segment], SPEC['anchors'][following]
    controls = {key: a['inferred_control_seeds'][key] * (1 - ease) + b['inferred_control_seeds'][key] * ease
                for key in a['inferred_control_seeds']}
    root = rig.pose.bones['mixamorig:Hips']
    dips = [0, 0, -.003, -.025, -.030, 0]
    root.matrix = Matrix.Translation((0, 0, -.010 + dips[segment] * (1 - ease) + dips[following] * ease)) @ root.matrix
    update()
    for name, factor in [('mixamorig:Spine', .35), ('mixamorig:Spine1', .35), ('mixamorig:Spine2', .30)]:
        quaternion = (Quaternion((0, 0, 1), math.radians(controls['torso_world_yaw_deg'] * factor)) @
                      Quaternion((1, 0, 0), math.radians(controls['torso_nose_down_pitch_deg'] * factor)))
        rotate(rig.pose.bones[name], quaternion)
    head = rig.pose.bones['mixamorig:Head']
    head_rotation = (Quaternion((0, 0, 1), math.radians(controls['head_world_yaw_deg'])) @
                     Quaternion((1, 0, 0), math.radians(controls['head_world_nose_down_pitch_deg'])) @
                     Quaternion((0, 1, 0), math.radians(controls['head_screen_clockwise_roll_deg'])))
    assign(head, head_rotation @ head.bone.matrix_local.to_quaternion(), head.head.copy())
    jaw_axis = head_rotation @ Vector((1, 0, 0))
    rotate(rig.pose.bones['Bone_025'], Quaternion(jaw_axis, math.radians(controls['clean_jaw_hinge_open_deg'])))
    for side, sign in [('Right', 1), ('Left', -1)]:
        key = side.lower()
        shoulder = rig.pose.bones['mixamorig:' + side + 'Shoulder']
        rotate(shoulder, Quaternion((0, 1, 0), math.radians(controls[key + '_clavicle_elevation_deg'] * sign)))
        upper, lower, hand = [rig.pose.bones['mixamorig:' + side + suffix] for suffix in ('Arm', 'ForeArm', 'Hand')]
        upper_length = (lower.bone.head_local - upper.bone.head_local).length
        lower_length = (hand.bone.head_local - lower.bone.head_local).length
        upper_target = interpolate_vector(direction_vector(a[key], 0, 1, upper_length),
                                          direction_vector(b[key], 0, 1, upper_length), u) * upper_length
        current = lower.head - upper.head
        rotate(upper, current.rotation_difference(upper_target))
        lower_target = interpolate_vector(direction_vector(a[key], 1, 2, lower_length),
                                          direction_vector(b[key], 1, 2, lower_length), u) * lower_length
        current = hand.head - lower.head
        rotate(lower, current.rotation_difference(lower_target))
        # Orient the palm from its actual digit bases, never from a guessed local bone axis.
        base_names = ['mixamorig:' + side + 'Hand' + d + '1' for d in ('Index', 'Middle', 'Pinky', 'Ring')]
        bases = [rig.data.bones[name].head_local for name in base_names]
        rest_long = sum(bases, Vector()) / len(bases) - hand.bone.head_local
        rest_width = bases[-1] - bases[0]
        rest_normal = rest_long.cross(rest_width).normalized()
        # Curl direction identifies the palm side on this mesh. The tiny signed Y
        # component of a cross product is not a reliable mirrored-hand classifier.
        tip_indices = [i for digit in ('Index', 'Middle', 'Pinky', 'Ring')
                       for i in TIP_MASKS[side + '_' + digit]]
        hook_direction = Vector(SOURCE['vertices'][tip_indices].mean(axis=0)) - sum(bases, Vector()) / len(bases)
        if rest_normal.dot(hook_direction) < 0:
            rest_normal.negate()
        rest_basis = palm_basis(rest_long, rest_normal)
        first_orientation = hand_anchor(side, a, hand, rest_basis, lower_length)
        second_orientation = hand_anchor(side, b, hand, rest_basis, lower_length)
        if first_orientation.dot(second_orientation) < 0:
            second_orientation.negate()
        desired_orientation = first_orientation.slerp(second_orientation, u)
        orient = desired_orientation.to_matrix()
        # Forearm pronation belongs on the forearm, not as an extreme wrist twist. Extract the
        # twist around elbow->wrist; this rotation preserves both joint centers exactly.
        difference = orient.to_quaternion() @ hand.matrix.to_quaternion().inverted()
        if difference.w < 0:
            difference.negate()
        axis = lower_target.normalized()
        along = Vector((difference.x, difference.y, difference.z)).dot(axis)
        twist_angle = 2 * math.atan2(along, difference.w)
        previous_angle = TWIST_HISTORY.get(side, twist_angle)
        while twist_angle - previous_angle > math.pi:
            twist_angle -= 2 * math.pi
        while twist_angle - previous_angle < -math.pi:
            twist_angle += 2 * math.pi
        TWIST_HISTORY[side] = twist_angle
        twist = Quaternion(axis, twist_angle)
        rotate(lower, twist)
        for number, fraction in enumerate((0, 1/3, 2/3)):
            helper = rig.pose.bones.get('Demon_' + side + '_ForearmTwist' + str(number))
            if helper:
                rotate(helper, Quaternion(axis, -twist_angle * (1 - fraction)))
        matrix = orient.to_4x4()
        matrix.translation = hand.head.copy()
        hand.matrix = matrix
        update()
        skin_orientation = desired_orientation @ hand.bone.matrix_local.to_quaternion().inverted()
        normal = skin_orientation @ rest_normal
        extension = controls[key + '_proximal_finger_straightening_fraction'] * .65
        fan = controls['right_fan_half_angle_deg'] if side == 'Right' else 3
        for digit, fan_sign in [('Index', 1), ('Middle', 1/3), ('Pinky', -1/3), ('Ring', -1)]:
            first, second, third = [rig.pose.bones['mixamorig:' + side + 'Hand' + digit + str(i)] for i in (1, 2, 3)]
            rotate(first, Quaternion(normal, math.radians((fan - 5) * fan_sign * sign)))
            first_direction, second_direction = second.head - first.head, third.head - second.head
            correction = second_direction.rotation_difference(first_direction)
            rotate(second, Quaternion().slerp(correction, extension))
        thumb = rig.pose.bones['mixamorig:' + side + 'HandThumb1']
        spread = controls['right_thumb_spread_deg'] - 10 if side == 'Right' else 0
        rotate(thumb, Quaternion(normal, math.radians(spread * sign)))
    for number, share in [(19, .30), (18, .25), (17, .20), (16, .15), (15, .10)]:
        rotate(rig.pose.bones['Bone_' + f'{number:03d}'], Quaternion((0, 0, 1), math.radians(controls['tail_total_world_z_yaw_deg'] * share)))
    for side in ('Right', 'Left'):
        foot = rig.pose.bones['mixamorig:' + side + 'Foot']
        group = list(SOURCE['group_names']).index(foot.name)
        rigid = SOURCE['weights'][:, group] > .999
        sole = float(SOURCE['vertices'][rigid, 2].min())
        target = foot.bone.head_local + Vector((0, 0, .002 - sole))
        solve_leg(rig, side, target)
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        if bone.name != 'mixamorig:Hips':
            bone.location = (0, 0, 0)
        bone.scale = (1, 1, 1)
    update()
    return {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}


def render(name, direction=(0, -6, 0), center=(0, -.10, .86), scale=2.35):
    scene, rig, mesh = objects()
    center = Vector(center)
    scene.camera.data.ortho_scale = scale
    scene.camera.location = center + Vector(direction)
    scene.camera.rotation_euler = (center - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(STAGE / (name + '.png'))
    bpy.ops.render.render(write_still=True)


def build():
    scene, rig, mesh = objects()
    scene.render.resolution_x = 1300
    scene.render.resolution_y = 1100
    if rig.animation_data:
        rig.animation_data.action = None
        for track in rig.animation_data.nla_tracks:
            track.mute = True
    TWIST_HISTORY.clear()
    samples = [pose_at(frame) for frame in range(37)]
    np.savez_compressed(STAGE / 'attack_baked_matrices.npz', times=np.arange(37)/48,
                        basis=np.array([[np.array(sample[b.name]) for b in rig.pose.bones] for sample in samples]),
                        bone_names=np.array([b.name for b in rig.pose.bones]))
    previous = bpy.data.actions.get('Demon_Native_Attack_v2')
    if previous:
        # Only this task-owned attack action is replaced when resuming authoring.
        for track in list(rig.animation_data.nla_tracks):
            if track.name == 'Attack':
                rig.animation_data.nla_tracks.remove(track)
        bpy.data.actions.remove(previous)
    action = bpy.data.actions.new('Demon_Native_Attack_v2')
    slot = action.slots.new(id_type='OBJECT', name=rig.name)
    layer = action.layers.new('Native attack sampled at 48 fps')
    strip = layer.strips.new(type='KEYFRAME')
    bag = strip.channelbag(slot, ensure=True)
    for bone in rig.pose.bones:
        values = [sample[bone.name].decompose() for sample in samples]
        quaternions = []
        for _, quaternion, _ in values:
            if quaternions and quaternion.dot(quaternions[-1]) < 0:
                quaternion.negate()
            quaternions.append(quaternion.copy())
        for prop, vectors in [('location', [value[0] for value in values]), ('rotation_quaternion', quaternions),
                              ('scale', [Vector((1, 1, 1)) for _ in values])]:
            path = 'pose.bones[' + json.dumps(bone.name) + '].' + prop
            for component in range(len(vectors[0])):
                curve = bag.fcurves.new(data_path=path, index=component)
                curve.keyframe_points.add(37)
                for point, frame, vector in zip(curve.keyframe_points, range(37), vectors):
                    point.co = (frame, vector[component])
                    point.interpolation = 'LINEAR'
                curve.update()
    rig.animation_data_create()
    for clip, duration, source_name in [('Walking', 50, 'Demon_Package_Walking'), ('Running', 32, 'Demon_Package_Running'), ('Attack', 36, action.name)]:
        track = next((t for t in rig.animation_data.nla_tracks if t.name == clip), None)
        if track is None:
            track = rig.animation_data.nla_tracks.new()
            track.name = clip
            nla_strip = track.strips.new(clip, 0, bpy.data.actions[source_name])
        else:
            nla_strip = track.strips[0]
            nla_strip.action = bpy.data.actions[source_name]
        nla_strip.action_slot = bpy.data.actions[source_name].slots[0]
        nla_strip.action_frame_start = nla_strip.frame_start = 0
        nla_strip.action_frame_end = nla_strip.frame_end = duration
        track.mute = True
    rig.animation_data.action = action
    rig.animation_data.action_slot = slot
    action.use_fake_user = True
    for index, letter in enumerate('abcdef'):
        scene.frame_set(index * 6)
        render('anchor_' + letter + '_front')
        render('anchor_' + letter + '_side', (6, 0, 0))
    scene.frame_set(24)
    render('preview')
    bpy.data.libraries.write(str(STAGE / 'attack_authored_checkpoint.blend'), {scene}, path_remap='RELATIVE')
    print('Keyed Attack: 37 poses at 48 fps, 0.750 s; Walking/Running retained.')
