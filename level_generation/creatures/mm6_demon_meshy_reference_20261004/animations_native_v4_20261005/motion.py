"""Native pose reconstruction on the repaired Meshy geometry. No source/baseline mutation."""
import bpy
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector

STAGE = Path(__file__).resolve().parent
STUDY = json.loads((STAGE.parent / 'animation_study/animation_motion_spec.json').read_text())
SOURCE = np.load(STAGE / 'source_geometry.npz')
TIP_MASKS = json.loads((STAGE.parent / 'attack_animation_v2/tip_vertex_masks.json').read_text())
# Reuse the already-reviewed rotation/hand-basis helpers. Do not execute their build entry point.
helpers = {'__file__': str(STAGE.parent / 'attack_animation_v2/motion.py'), '__name__': 'pose_helpers'}
exec(compile(Path(helpers['__file__']).read_text(), helpers['__file__'], 'exec'), helpers)
rotate, assign, direction_vector, palm_basis = [helpers[n] for n in ('rotate', 'assign', 'direction_vector', 'palm_basis')]

ENDS = {'Standing': 6, 'Walk_Native': 54, 'Hit': 36, 'Fidget': 30, 'Death': 60, 'Ash_Remains': 6}
SOURCE_ACTION = {'Standing': 'standing', 'Walk_Native': 'walk', 'Hit': 'hit', 'Fidget': 'fidget',
                 'Death': 'death', 'Ash_Remains': 'corpse'}
# All degree values below are restrained authored interpretations, not recovered joint angles.
CONTROLS = {
    'Standing': dict(dip=[0], yaw=[0], head=[0], roll=[0], pitch=[0], jaw=[0], tail=[5],
                     extensionR=[.12], extensionL=[.12], fanR=[5], fanL=[5], palmR=[.25], palmL=[.30]),
    'Walk_Native': dict(dip=[0, -.070, .010, 0, -.070, .010], yaw=[-2, -4, -2, 2, 4, 2],
                        head=[0, -2.5, 1.5, 0, 2.5, -1.5], roll=[0, 1, 0, 0, -1, 0],
                        pitch=[0, 2, -1, 0, 2, -1], jaw=[1, 4, 1, 2, 4, 1], tail=[9, 13, 6, -9, -13, -6],
                        extensionR=[.12, .06, .30, .20, .12, .30], extensionL=[.25, .40, .12, .15, .06, .30],
                        fanR=[5, 3, 10, 7, 4, 9], fanL=[8, 12, 5, 5, 3, 10],
                        palmR=[.25, .10, .60, .40, .12, .35], palmL=[.40, .12, .25, .25, .45, .60]),
    'Hit': dict(dip=[0, 0, -.008, -.012, -.008, 0], yaw=[0, -2, -4, -7, -4, -2],
                head=[0, 2, 4, 8, 4, 2], roll=[0, -2, -4, -12, -4, -2],
                pitch=[0, -5, -10, -40, -10, -5], jaw=[0, 3, 6, 10, 6, 3], tail=[5, 8, 13, 36, 13, 8],
                recoil=[0, .10, .30, 1, .30, .10],
                extensionR=[.12, .22, .40, .65, .40, .22], extensionL=[.12, .22, .50, 1.30, .50, .22],
                fanR=[5, 7, 10, 17, 10, 7], fanL=[5, 7, 12, 18, 12, 7],
                palmR=[.25, .40, .65, .75, .65, .40], palmL=[.30, .35, .65, .60, .65, .35]),
    'Fidget': dict(dip=[0, -.016, -.033, -.055, -.033], yaw=[0, 0, 0, 0, 0],
                   head=[0, 0, 0, 0, 0], roll=[0, 0, 0, 0, 0], pitch=[0, 1, 2, 4, 2],
                   jaw=[0, 5, 10, 14, 10], tail=[5, 6, 7, 8, 7],
                   extensionR=[.12, .20, .40, .75, .40], extensionL=[.12, .20, .40, .75, .40],
                   fanR=[5, 7, 12, 18, 12], fanL=[5, 7, 12, 18, 12],
                   palmR=[.25, .35, .60, .80, .60], palmL=[.30, .35, .60, .80, .60]),
    'Death': dict(dip=[0, -.004, -.010, -.012, -.012, -.012, -.012, -.012, -.012],
                  yaw=[0, 0, -3, -3, -3, -3, -3, -3, -3], head=[0, 0, 4, 4, 4, 4, 4, 4, 4],
                  roll=[0, 0, -3, -3, -3, -3, -3, -3, -3], pitch=[0, -3, -12, -12, -12, -12, -12, -12, -12],
                  jaw=[0, 4, 12, 12, 12, 12, 12, 12, 12], tail=[5, 8, 12, 12, 12, 12, 12, 12, 12],
                  extensionR=[.12, .3, .7, .7, .7, .7, .7, .7, .7], extensionL=[.12, .3, .7, .7, .7, .7, .7, .7, .7],
                  fanR=[5, 8, 17, 17, 17, 17, 17, 17, 17], fanL=[5, 8, 18, 18, 18, 18, 18, 18, 18],
                  palmR=[.25, .4, .8, .8, .8, .8, .8, .8, .8], palmL=[.30, .4, .75, .75, .75, .75, .75, .75, .75]),
}
CONTROLS['Ash_Remains'] = CONTROLS['Standing']
TWIST_HISTORY = {}


def objects():
    scene = bpy.data.scenes['MM6_Demon_Native_Animations']
    bpy.context.window.scene = scene
    return scene, scene.objects['Demon_Native_Rig'], scene.objects['Demon_Native_Mesh']


def phase(clip, frame):
    action = 'standing' if clip == 'Ash_Remains' else SOURCE_ACTION[clip]
    c = STUDY['clips'][action]
    anchors = c['anchors']
    times = [a['sample'] for a in anchors]
    index = max(i for i, t in enumerate(times) if t <= frame + 1e-8)
    following = index + 1 if index + 1 < len(times) else 0 if c['loop'] else index
    length = anchors[index]['hold_ms'] * 48 / 1000
    u = max(0, min(1, (frame - times[index]) / length))
    return index, following, u, u * u * (3 - 2 * u)


def leg(rig, side, target, orientation, yaw=0):
    upper, lower, foot = [rig.pose.bones['mixamorig:' + side + s] for s in ('UpLeg', 'Leg', 'Foot')]
    a = lower.bone.head_local - upper.bone.head_local
    b = foot.bone.head_local - lower.bone.head_local
    l1, l2 = a.length, b.length
    hip = upper.head.copy()
    delta = target - hip
    distance = delta.length
    assert abs(l1 - l2) < distance < l1 + l2, (side, distance, l1 + l2)
    axis = delta.normalized()
    forward = Quaternion((0, 0, 1), yaw) @ Vector((0, -1, 0))
    pole = (forward - axis * forward.dot(axis)).normalized()
    along = (l1*l1 - l2*l2 + distance*distance) / (2*distance)
    knee = hip + axis*along + pole*math.sqrt(max(0, l1*l1 - along*along))
    assign(upper, a.rotation_difference(knee - hip) @ upper.bone.matrix_local.to_quaternion(), hip)
    assign(lower, b.rotation_difference(target - knee) @ lower.bone.matrix_local.to_quaternion(), knee)
    assign(foot, orientation, target)


def pose_at(clip, frame):
    scene, rig, mesh = objects()
    for bone in rig.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    index, following, u, ease = phase(clip, frame)
    controls = {k: v[index] * (1-ease) + v[following] * ease for k, v in CONTROLS[clip].items()}
    action = 'standing' if clip == 'Ash_Remains' else SOURCE_ACTION[clip]
    landmarks = STUDY['clips'][action]['landmarks']['0']
    # Death's hidden pose is held from its last visible anchor; it is not inferred from flame tips.
    a, b = landmarks[min(index, 2 if clip == 'Death' else index)], landmarks[min(following, 2 if clip == 'Death' else following)]
    root = rig.pose.bones['mixamorig:Hips']
    root.matrix = Matrix.Translation((0, 0, -.010 + controls['dip'])) @ root.matrix
    bpy.context.view_layer.update()
    for name, share in [('Spine', .35), ('Spine1', .35), ('Spine2', .30)]:
        rotate(rig.pose.bones['mixamorig:' + name], Quaternion((0, 0, 1), math.radians(controls['yaw'] * share)))
    head = rig.pose.bones['mixamorig:Head']
    head_q = (Quaternion((0, 0, 1), math.radians(controls['head'])) @
              Quaternion((1, 0, 0), math.radians(controls['pitch'])) @
              Quaternion((0, 1, 0), math.radians(controls['roll'])))
    assign(head, head_q @ head.bone.matrix_local.to_quaternion(), head.head.copy())
    rotate(rig.pose.bones['Bone_025'], Quaternion(head_q @ Vector((1, 0, 0)), math.radians(controls['jaw'])))
    for side, sign in [('Right', 1), ('Left', -1)]:
        key = side.lower() + '_arm'
        if clip == 'Hit':
            rotate(rig.pose.bones['mixamorig:'+side+'Shoulder'],
                   Quaternion((0, 1, 0), math.radians((4 if side == 'Right' else 10)*sign*controls['recoil'])))
        upper, lower, hand = [rig.pose.bones['mixamorig:' + side + s] for s in ('Arm', 'ForeArm', 'Hand')]
        upper_length = (lower.bone.head_local - upper.bone.head_local).length
        lower_length = (hand.bone.head_local - lower.bone.head_local).length
        targets = []
        for start, end, length in [(0, 1, upper_length), (1, 2, lower_length)]:
            p = direction_vector(a[key], start, end, length)
            q = direction_vector(b[key], start, end, length)
            targets.append((p * (1-u) + q*u).normalized() * length)
        if clip == 'Hit' and side == 'Left':
            # Compensate for this model's taller head/shorter projected arm; preserve actual forearm length.
            targets[1].z += .10*controls['recoil']
            projected = math.hypot(targets[1].x, targets[1].z)
            if projected > lower_length*.985:
                targets[1].x *= lower_length*.985/projected
                targets[1].z *= lower_length*.985/projected
            targets[1].y = -math.sqrt(lower_length**2-targets[1].x**2-targets[1].z**2)
        rotate(upper, (lower.head - upper.head).rotation_difference(targets[0]))
        rotate(lower, (hand.head - lower.head).rotation_difference(targets[1]))
        bases = [rig.data.bones['mixamorig:' + side + 'Hand' + d + '1'].head_local
                 for d in ('Index', 'Middle', 'Pinky', 'Ring')]
        rest_long = sum(bases, Vector()) / 4 - hand.bone.head_local
        rest_normal = rest_long.cross(bases[-1] - bases[0]).normalized()
        tips = [i for d in ('Index', 'Middle', 'Pinky', 'Ring') for i in TIP_MASKS[side + '_' + d]]
        hook = Vector(SOURCE['vertices'][tips].mean(0)) - sum(bases, Vector()) / 4
        if rest_normal.dot(hook) < 0:
            rest_normal.negate()
        rest_basis = palm_basis(rest_long, rest_normal)
        orientations = []
        for points in (a[key], b[key]):
            desired = Vector(((points[3][0]-points[2][0])*.0065, -.065,
                              (points[2][1]-points[3][1])*.0065)).normalized()
            bend = targets[1].normalized().rotation_difference(desired)
            if bend.angle > math.radians(40):
                desired = Quaternion().slerp(bend, math.radians(40)/bend.angle) @ targets[1].normalized()
            frontal = controls['palm' + side[0]]
            normal = Vector((sign * (.9 * (1-frontal) + .35*frontal), -.25-.75*frontal, 0))
            basis = palm_basis(desired, normal)
            orientations.append((basis @ rest_basis.transposed() @ hand.bone.matrix_local.to_3x3()).to_quaternion())
        if orientations[0].dot(orientations[1]) < 0:
            orientations[1].negate()
        desired = orientations[0].slerp(orientations[1], u)
        difference = desired @ hand.matrix.to_quaternion().inverted()
        if difference.w < 0:
            difference.negate()
        axis = targets[1].normalized()
        angle = 2*math.atan2(Vector((difference.x, difference.y, difference.z)).dot(axis), difference.w)
        previous = TWIST_HISTORY.get(side, angle)
        while angle-previous > math.pi:
            angle -= 2*math.pi
        while angle-previous < -math.pi:
            angle += 2*math.pi
        TWIST_HISTORY[side] = angle
        rotate(lower, Quaternion(axis, angle))
        for number, fraction in enumerate((0, 1/3, 2/3)):
            rotate(rig.pose.bones[f'Demon_{side}_ForearmTwist{number}'], Quaternion(axis, -angle*(1-fraction)))
        assign(hand, desired, hand.head.copy())
        normal = (desired @ hand.bone.matrix_local.to_quaternion().inverted()) @ rest_normal
        for d, spread in [('Index', 1), ('Middle', 1/3), ('Pinky', -1/3), ('Ring', -1)]:
            first, second, third = [rig.pose.bones[f'mixamorig:{side}Hand{d}{i}'] for i in (1, 2, 3)]
            rotate(first, Quaternion(normal, math.radians((controls['fan'+side[0]]-5)*spread*sign)))
            correction = (third.head-second.head).rotation_difference(second.head-first.head)
            rotate(second, Quaternion().slerp(correction, controls['extension'+side[0]]*.65))
        rotate(rig.pose.bones['mixamorig:' + side + 'HandThumb1'],
               Quaternion(normal, math.radians((controls['fan'+side[0]]-5)*.55*sign)))
    # Retain a bent root-to-tip curve: increasingly hanging distal segments, plus distributed yaw/lag.
    rotate(rig.pose.bones['Bone_020'], Quaternion((1, 0, 0), math.radians(20)))
    tail_bends = [25, -65, -45, 10, 5]
    for i, (number, share, bend) in enumerate(zip(range(19, 14, -1), [.30, .25, .20, .15, .10], tail_bends)):
        bone = rig.pose.bones[f'Bone_{number:03d}']
        lag = 2 * math.sin(frame*2*math.pi/54 - i*.45) if clip == 'Walk_Native' else 0
        rotate(bone, Quaternion((1, 0, 0), math.radians(bend + lag)))
        rotate(bone, Quaternion((0, 0, 1), math.radians(controls['tail']*share)))
    # Fit the native front-view tip while retaining the entire curved chain and its physical length.
    # The missing depth is inferred behind the hips. Hit D lifts the curved tail sideways at waist height.
    tail_a, tail_b = a.get('tail', []), b.get('tail', [])
    if clip == 'Death':
        # C's tail is occluded: keep the last observed B tip instead of measuring the plume.
        tail_a, tail_b = landmarks[min(index, 1)]['tail'], landmarks[min(following, 1)]['tail']
    if tail_a and tail_b:
        point = Vector(tail_a[0]).lerp(Vector(tail_b[0]), ease)
        base = rig.pose.bones['Bone_019']
        chord = rig.pose.bones['Bone_015'].tail-base.head
        dx, dz = (point.x-177)*.0065-base.head.x, (330-point.y)*.0065-base.head.z
        projected = math.hypot(dx, dz)
        if projected > chord.length*.98:
            dx, dz = dx*chord.length*.98/projected, dz*chord.length*.98/projected
        target = Vector((dx, math.sqrt(chord.length**2-dx*dx-dz*dz), dz))
        rotate(base, chord.rotation_difference(target))
    for side in ('Right', 'Left'):
        foot = rig.pose.bones['mixamorig:' + side + 'Foot']
        shift, lift, pitch, yaw, lateral = 0, 0, 0, 0, 0
        if clip == 'Walk_Native':
            offset = 0 if side == 'Right' else 3
            values = [(0, .035, 0), (-.16, .006, -22), (.045, 0, 10),
                      (0, 0, 0), (.12, .006, 16), (.30, .22, 40)]
            p, q = values[(index+offset)%6], values[(following+offset)%6]
            shift, lift, pitch = [p[k]*(1-ease)+q[k]*ease for k in range(3)]
        elif clip == 'Hit' and side == 'Left':
            lifts = [0, .022, .055, .070, .055, .022]
            pitches = [0, -8, -15, -20, -15, -8]
            lift = lifts[index]*(1-ease)+lifts[following]*ease
            pitch = pitches[index]*(1-ease)+pitches[following]*ease
        elif clip in ('Hit', 'Fidget'):
            if side == 'Right':
                yaws = [0, 2, 4, 6, 4, 2] if clip == 'Hit' else [0, 2, 4, 6, 4]
                shifts = [0, .003, .006, .009, .006, .003] if clip == 'Hit' else [0, .006, .013, .020, .013]
            else:
                yaws, shifts = [0, .5, 1, 1.5, 1], [0, .001, .002, .003, .002]
            yaw = yaws[index]*(1-ease)+yaws[following]*ease
            lateral = shifts[index]*(1-ease)+shifts[following]*ease
        orientation = (Quaternion((0, 0, 1), math.radians(yaw)) @
                       Quaternion((1, 0, 0), math.radians(pitch)) @ foot.bone.matrix_local.to_quaternion())
        transform = orientation.to_matrix() @ foot.bone.matrix_local.to_3x3().inverted()
        rigid = SOURCE['weights'][:, list(SOURCE['group_names']).index(foot.name)] > .999
        local = SOURCE['vertices'][rigid] - np.array(foot.bone.head_local)
        min_z = float((local @ np.array(transform).T)[:, 2].min())
        target = foot.bone.head_local.copy()
        target.y += shift
        target.x += lateral
        target.z = .006 + lift - min_z
        leg(rig, side, target, orientation, math.radians(yaw*.35))
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        if bone.name != 'mixamorig:Hips':
            bone.location = (0, 0, 0)
        bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    return {b.name: b.matrix_basis.copy() for b in rig.pose.bones}


def bake_action(clip, pose=None, end=None):
    scene, rig, mesh = objects()
    rig.animation_data.action = None
    TWIST_HISTORY.clear()
    if pose is None:
        pose = pose_at
    samples = [pose(clip, f) for f in range((ENDS[clip] if end is None else end)+1)]
    action = bpy.data.actions.new('DemonNative_' + clip)
    slot = action.slots.new(id_type='OBJECT', name=rig.name)
    bag = action.layers.new('Native 48 fps').strips.new(type='KEYFRAME').channelbag(slot, ensure=True)
    for bone in rig.pose.bones:
        values = [sample[bone.name].decompose() for sample in samples]
        rotations = []
        for _, q, _ in values:
            if rotations and q.dot(rotations[-1]) < 0:
                q.negate()
            rotations.append(q)
        for prop, vectors in [('location', [v[0] for v in values]), ('rotation_quaternion', rotations),
                              ('scale', [Vector((1, 1, 1)) for v in values])]:
            for component in range(len(vectors[0])):
                curve = bag.fcurves.new('pose.bones[' + json.dumps(bone.name) + '].' + prop, index=component)
                curve.keyframe_points.add(len(samples))
                for f, point in enumerate(curve.keyframe_points):
                    point.co = (f, vectors[f][component])
                    point.interpolation = 'LINEAR'
                curve.update()
    action.use_fake_user = True
    track = rig.animation_data.nla_tracks.new()
    track.name = clip
    strip = track.strips.new(clip, 0, action)
    strip.action_slot = slot
    track.mute = True
    np.savez_compressed(STAGE / (clip + '_baked.npz'),
                        basis=np.array([[np.array(sample[b.name]) for b in rig.pose.bones] for sample in samples]),
                        bone_names=np.array([b.name for b in rig.pose.bones]))
    print('Authored', clip, len(samples), 'poses', flush=True)
    return action


def activate(clip, frame=0):
    scene, rig, mesh = objects()
    for obj in scene.objects:
        for owner in [obj, obj.data.shape_keys if obj.type == 'MESH' else None]:
            if owner is None or owner.animation_data is None:
                continue
            owner.animation_data.action = None
            for track in owner.animation_data.nla_tracks:
                track.mute = track.name != clip
    scene.frame_start, scene.frame_end = 0, ENDS.get(clip, {'Attack': 36, 'Walking': 50, 'Running': 32}.get(clip, 6))
    scene.frame_set(int(frame), subframe=float(frame%1))
    bpy.context.view_layer.update()
