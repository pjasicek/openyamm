"""Native action intent and timing, authored on this skeleton and sampled into portable FK channels."""
import json
import math
import traceback

import bpy
from mathutils import Vector, Quaternion

import pose
from mesh_tools import ROOT

FPS = 48
WALK_PHASES = [('.L', .5), ('.R', 0)]  # Frame 1 matches native b: right leg and left arm forward.
WALK_STANCE = .68


def sample(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t <= b:
            f = (t - a) / (b - a)
            f = f * f * (3 - 2 * f)
            if isinstance(va, (list, tuple, Vector)):
                return Vector(va).lerp(Vector(vb), f)
            return va + (vb - va) * f
    return keys[-1][1]


def path(keys, t):
    """C1 motion through control poses; intermediate cut keys do not stop the swing."""
    vectors = isinstance(keys[0][1], (list, tuple, Vector))
    values = [Vector(value) if vectors else value for time, value in keys]
    if t <= keys[0][0]:
        return values[0]
    if t >= keys[-1][0]:
        return values[-1]
    for i in range(len(keys) - 1):
        a, b = keys[i][0], keys[i + 1][0]
        if t <= b:
            interval = b - a
            u = (t - a) / interval
            ma = (values[i + 1] - values[i - 1]) / (b - keys[i - 1][0]) if i else values[0] * 0
            mb = ((values[i + 2] - values[i]) / (keys[i + 2][0] - a)
                  if i + 2 < len(keys) else values[-1] * 0)
            return ((2 * u**3 - 3 * u**2 + 1) * values[i] + (u**3 - 2 * u**2 + u) * interval * ma
                    + (-2 * u**3 + 3 * u**2) * values[i + 1] + (u**3 - u**2) * interval * mb)


# Native attack A–F are six front-facing poses, each displayed for 0.125 s.
# A is a distinct attack guard: elbow down, hilt ahead of the hip, blade across the torso.
ATTACK_WRIST = [(0, (-.265, -.205, .96)), (1/6, (.18, -.205, 1.365)),
                (2/6, (.205, -.215, 1.385)), (2.5/6, (-.16, -.385, 1.205)),
                (3/6, (-.38, -.22, 1.07)),
                (4/6, (-.44, -.25, 1.035)), (5/6, (-.35, -.18, 1.005)),
                (1, (-.265, -.205, .96))]
ATTACK_HAND = json.loads((ROOT / 'authoring/attack_hand_rotations.json').read_text())['keys']


def pelvis_offset(x=0, y=0, z=-.025):
    arm = pose.rig()
    arm.pose.bones['pelvis'].location = arm.data.bones['pelvis'].matrix_local.to_quaternion().inverted() @ Vector((x, y, z))
    pose.update()


def walk(t):
    pose.standing(t)
    cycle = math.tau * t
    turn = math.cos(cycle)
    sway = math.sin(cycle)
    # Native b/e expose opposite chest/back faces. Spread the twist through the waist and ribcage.
    # The body drops at contact and rises over the supporting leg, with a persistent forward lean.
    pelvis_offset(z=-.058 - .018 * math.cos(cycle * 2), x=-.022 * sway)
    pose.local('pelvis', (6, 10 * turn, 2 * sway))
    pose.local('spine', (9, -27 * turn, -1.5 * sway))
    pose.local('chest', (-2, -18 * turn, 0))
    pose.local('neck', (-3, 6 * turn, 0))
    pose.local('head', (-9 + 2 * sway, 16 * turn, -sway))
    swings = []
    for suffix, offset in WALK_PHASES:
        p = (t + offset) % 1
        if p <= WALK_STANCE:
            q = p / WALK_STANCE
            y = -.30 + q * .80
            # Native b/e contact frames land toes-up; c/f show a pronounced raised heel.
            angle = sample([(0, -26), (.18, 0), (.74, 0), (1, 38)], q)
            lift = 0
        else:
            q = (p - WALK_STANCE) / (1 - WALK_STANCE)
            y = .50 - .80 * (q * q * (3 - 2 * q))
            lift = .115 * math.sin(q * math.pi) ** 2
            angle = sample([(0, 38), (.25, 20), (.65, -10), (.9, -26), (1, -26)], q)
        ankle = pose.MARKS['ankle' + suffix].copy()
        roll_y, contact_z = pose.foot_contact_offset(suffix, angle)
        ankle.y, ankle.z = y + roll_y, contact_z + lift
        pose.foot(suffix, ankle, angle)
        swings.append(math.degrees(math.atan2(.05 - y, .68)))
    # Arms counter the opposite legs. Drive the upper arms, then let softly bent elbows follow.
    right_swing = 2 - 24 * turn
    left_swing = 2 + 26 * turn
    pose.swing_arm('.R', right_swing, bend=30, spread=18)
    pose.swing_arm('.L', left_swing, bend=22, spread=18)
    elevation = math.radians(4 + 1.35 * right_swing)
    blade = pose.chest_rotation() @ Vector((.08, -math.cos(elevation), math.sin(elevation)))
    pose.hand_orientation('.R', blade, down=pose.rig().pose.bones['forearm.R'].vector)
    pose.grip()
    pose.free_hand(palm=pose.chest_rotation() @ Vector((-1, 0, 0)))
    pose.skirt(*swings, crouch=3)


def attack(t):
    pose.standing()
    yaw = path([(0, 0), (1/6, 22), (2/6, 13), (3/6, -2), (4/6, -22), (5/6, -12), (1, 0)], t)
    lean = path([(0, 1.5), (.30, -3), (.64, 10), (1, 1.5)], t)
    pelvis_offset(x=path([(0, 0), (.32, .018), (.65, -.035), (1, 0)], t),
                  y=path([(0, 0), (.33, 0), (.67, -.08), (1, 0)], t), z=-.025)
    pose.local('spine', (lean, yaw * .55, 0))
    pose.local('chest', (-1.5, yaw, 0))
    raise_head = path([(0, 0), (1/6, 1), (2/6, .50), (3/6, 0), (4/6, -.35), (5/6, -.15), (1, 0)], t)
    pose.local('neck', (-3 * raise_head, 0, 0))
    pose.local('head', (-17 * raise_head, 5 * raise_head - yaw * .15, 2 * raise_head))
    wrist = path(ATTACK_WRIST, t)
    hand_rotation = Quaternion(path(ATTACK_HAND, t)).normalized()
    # B/C lift the humerus across the chest. The elbow follows forward below the hilt,
    # rather than staying out beside the ribs while only the forearm lifts.
    pole = path([(0, (-.44, .04, 1.06)), (1/6, (-.029, -.247, 1.312)),
                 (2/6, (-.001, -.156, 1.335)), (2.5/6, (-.37, -.18, 1.10)),
                 (3/6, (-.50, .03, 1.10)),
                 (4/6, (-.55, .03, 1.06)), (5/6, (-.50, .04, 1.08)),
                 (1, (-.44, .04, 1.06))], t)
    # Keep the elbow on its own anatomical path. Deriving its pole from the hand
    # orientation pulled it above the shoulder during the cut and reversed its bend.
    pose.limb('upper_arm.R', 'forearm.R', wrist, pole, hinge=True)
    forearm = pose.rig().pose.bones['forearm.R'].vector.normalized()
    hand_axis = hand_rotation @ Vector((0, 1, 0))
    bend = hand_axis.angle(forearm)
    if bend > math.radians(35):
        correction = hand_axis.rotation_difference(forearm)
        hand_rotation = Quaternion().slerp(correction, 1 - math.radians(35) / bend) @ hand_rotation
    pose.set_hand_rotation('.R', hand_rotation.to_matrix().to_4x4())
    pose.grip()
    # The native free hand cups upward under the hilt in B/C, then opens and sweeps
    # across the abdomen in D/E. It neither hangs through the cut nor follows the sword.
    left_wrist = path([(0, (.275, -.095, .905)), (1/6, (.29, -.20, 1.18)),
                       (2/6, (.255, -.175, 1.255)), (3/6, (.045, -.30, 1.09)),
                       (4/6, (-.02, -.29, .96)), (5/6, (.13, -.27, .925)),
                       (1, (.275, -.095, .905))], t)
    left_pole = path([(0, (.285, .065, 1.095)), (1/6, (.33, .025, 1.09)),
                      (2/6, (.32, -.055, 1.10)), (3/6, (.29, -.15, 1.14)),
                      (4/6, (.25, -.07, 1.10)), (5/6, (.28, -.08, 1.09)),
                      (1, (.285, .065, 1.095))], t)
    pose.limb('upper_arm.L', 'forearm.L', left_wrist, left_pole, hinge=True)
    left_direction = path([(0, (-.10, -.25, -.96)), (1/6, (.50, -.80, .28)),
                           (2/6, (-.15, -.40, .90)), (3/6, (-.88, -.40, -.20)),
                           (4/6, (-.78, -.50, -.35)), (5/6, (-.40, -.45, -.80)),
                           (1, (-.10, -.25, -.96))], t)
    left_palm = path([(0, (-1, 0, 0)), (1/6, (-.30, -.45, .84)),
                      (2/6, (-.50, -.85, 0)), (3/6, (0, -1, .25)),
                      (4/6, (0, -.8, .60)), (5/6, (-.45, -.85, .20)),
                      (1, (-1, 0, 0))], t)
    pose.free_hand(direction=left_direction, palm=left_palm)
    curl = sample([(0, 1), (1/6, 2.2), (2/6, 2), (3/6, .30), (4/6, .20), (5/6, .45), (1, 1)], t)
    for finger in range(4):
        for joint, angle in enumerate([15, 22, 16]):
            pose.rig().pose.bones[f'digit.L.{finger}.{joint + 1:02}'].rotation_quaternion = \
                Quaternion((1, 0, 0), math.radians(-angle * curl))
    for suffix in ['.L', '.R']:
        ankle = pose.MARKS['ankle' + suffix].copy()
        if suffix == '.L':
            ankle.z += sample([(0, 0), (.18, .10), (.33, .075), (.53, 0), (1, 0)], t)
            ankle.y += sample([(0, 0), (.32, -.095), (.58, -.035), (1, 0)], t)
        pose.foot(suffix, ankle)
    pose.skirt(16 * math.sin(math.pi * t), -3, crouch=2)


def hit(t):
    pose.standing()
    if t <= 0 or t >= 1:
        return
    amount = sample([(0, 0), (.23, 1), (.49, .86), (.74, .40), (1, 0)], t)
    pose.local('spine', (-12 * amount, -6 * amount, 5 * amount))
    pose.local('chest', (13 * amount, -8 * amount, -3 * amount))
    pose.local('head', (18 * amount, 20 * amount, 0))
    left = Vector((.315, -.032, .88)).lerp(Vector((-.13, -.20, 1.51)), amount)
    pose.limb('upper_arm.L', 'forearm.L', left, (.30, -.22, 1.29))
    pose.free_hand(direction=pose.rig().pose.bones['forearm.L'].vector.normalized().lerp(Vector((-.85, -.10, .36)), amount),
                   palm=Vector((-1, 0, 0)).lerp(Vector((0, 1, 0)), amount))
    pose.limb('upper_arm.R', 'forearm.R', Vector((-.287, -.116, .986)).lerp(Vector((-.42, -.13, 1.01)), amount),
              (-.43, .04, 1.13))
    pose.hand_orientation('.R', Vector((.08, -.995, .035)).lerp(Vector((.12, -.34, .93)), amount))
    pose.grip()
    pose.skirt(0, 0, crouch=3 * amount)


def fidget(t):
    pose.standing()
    if t <= 0 or t >= 1:
        return
    s = math.sin(t * math.tau)
    pose.local('head', (-2 * math.sin(t * math.pi), 8 * s, 0))
    pose.local('chest', (-1.5, 2 * s, 0))
    pose.limb('upper_arm.R', 'forearm.R', (-.287, -.116 - .018 * math.sin(math.pi * t), .986 + .018 * math.sin(math.pi * t)),
              (-.44, .015, 1.11))
    pose.hand_orientation('.R', (.08 + .035 * s, -.995, .035 + .03 * s))
    pose.grip()


def death(t):
    pose.standing()
    if t <= 0:
        return
    arm = pose.rig()
    angle = sample([(0, 0), (.24, 17), (.49, 39), (.76, 79), (.91, 91), (1, 90)], t)
    z = sample([(0, 0), (.24, -.15), (.49, -.21), (.76, .04), (.91, .185), (1, .19)], t)
    arm.pose.bones['root'].rotation_quaternion = Quaternion((1, 0, 0), math.radians(angle))
    arm.pose.bones['root'].location = arm.data.bones['root'].matrix_local.to_quaternion().inverted() @ \
        Vector((0, .20 * t, z))
    pelvis_offset(z=0)
    pose.local('spine', (sample([(0, 1.5), (.40, 18), (.76, 3), (1, 0)], t), 0, 0))
    pose.local('chest', (-1, 0, 0))
    pose.local('head', (sample([(0, 0), (.4, 15), (1, -3)], t), 8 * t, 0))
    for suffix in ['.L', '.R']:
        side = 1 if suffix == '.L' else -1
        target = sample([(0, (side * .142, .089, .12)), (.48, (side * .18, .07, .125)),
                         (.76, (side * .215, .06, .12)), (1, (side * .235, .07, .12))], t)
        pole = Vector((side * .30, -.42 + .25 * t, .47 - .19 * t))
        pose.limb('thigh' + suffix, 'shin' + suffix, target, pole)
        direction = Vector((0, -.255, -.093)).lerp(Vector((0, .22, -.10)), t)
        pose.aim('foot' + suffix, direction)
        pb = arm.pose.bones['foot' + suffix]
        deform = pb.matrix @ pb.bone.matrix_local.inverted()
        lows = []
        for objname in ['GB15 Skin body', 'GB15 Claws']:
            obj = bpy.data.objects[objname]
            group = obj.vertex_groups['foot' + suffix].index
            lows.extend((deform @ v.co).z for v in obj.data.vertices
                        if any(entry.group == group and entry.weight > .99 for entry in v.groups))
        if min(lows) < .002:
            target = Vector(target)
            target.z += .002 - min(lows)
            pose.limb('thigh' + suffix, 'shin' + suffix, target, pole)
            pose.aim('foot' + suffix, direction)
    right = sample([(0, (-.287, -.116, .986)), (.28, (-.12, -.25, .76)),
                    (.56, (-.29, -.60, .42)), (.78, (-.47, -1.06, .15)), (1, (-.48, -1.18, .11))], t)
    left = sample([(0, (.315, -.032, .88)), (.3, (.18, -.28, .78)),
                   (.56, (.29, -.58, .42)), (.78, (.53, -1.08, .14)), (1, (.55, -1.20, .09))], t)
    pose.limb('upper_arm.R', 'forearm.R', right, (-.54, -.55, .28))
    pose.limb('upper_arm.L', 'forearm.L', left, (.63, -.64, .22))
    blade = Vector((.08, -.995, .035)).lerp(Vector((-.80, -.60, .02)), t)
    down = Vector((0, 0, -1)).lerp(Vector((.60, -.80, 0)), t)
    pose.hand_orientation('.R', blade, down=down)
    pose.grip()
    pose.free_hand(direction=Vector((-.12, -.29, -.95)).lerp(Vector((.65, -.72, -.04)), t),
                   palm=Vector((-1, 0, 0)).lerp(Vector((0, 0, -1)), t))
    # Spread the unarmed fingers against the floor in the final pose.
    for finger in range(4):
        for joint in range(3):
            arm.pose.bones[f'digit.L.{finger}.{joint + 1:02}'].rotation_quaternion = \
                Quaternion((1, 0, 0), math.radians(-12 * (1 - t)))
    pose.skirt(0, 0, crouch=14 * t)


def ground_correct():
    graph = bpy.context.evaluated_depsgraph_get()
    low = min((obj.evaluated_get(graph).matrix_world @ vertex.co).z
              for obj in bpy.data.collections['GB15 Character'].objects if obj.type == 'MESH'
              for vertex in obj.evaluated_get(graph).data.vertices)
    correction = max(0, .001 - low)
    if correction:
        root = pose.rig().pose.bones['root']
        root.location += root.bone.matrix_local.to_quaternion().inverted() @ Vector((0, 0, correction))
        pose.update()
    return correction


CLIPS = [('standing', 2., 8, pose.standing), ('walk', 1., 1, walk), ('attack', .75, 1, attack),
         ('hit', .75, 2, hit), ('death', .625, 2, death), ('corpse', 1., 48, lambda t: death(1)),
         ('fidget', .75, 3, fidget)]


def author(clip_names=None):
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.render.fps_base = 1
    arm = pose.rig()
    arm.animation_data_create()
    queue = [clip for clip in CLIPS if clip_names is None or clip[0] in clip_names]
    manifest_path = ROOT / 'authoring/clips.json'
    manifest = ([entry for entry in json.loads(manifest_path.read_text()) if entry['name'] not in clip_names]
                if clip_names is not None else [])
    status = ROOT / 'authoring/motion_status.json'

    def step():
        try:
            if not queue:
                (ROOT / 'authoring/clips.json').write_text(json.dumps(manifest, indent=2) + '\n')
                status.write_text(json.dumps({'state': 'complete', 'clips': [c['name'] for c in manifest]}))
                activate('standing')
                return None
            name, duration, spacing, function = queue.pop(0)
            status.write_text(json.dumps({'state': 'authoring', 'clip': name}))
            existing = bpy.data.actions.get(name)
            if existing and existing.get('gb_owner') == 'Authored goblin':
                bpy.data.actions.remove(existing)
            action = bpy.data.actions.new(name)
            action['gb_owner'] = 'Authored goblin'
            action['duration_seconds'] = duration
            action.use_fake_user = True
            arm.animation_data.action = action
            length = round(duration * FPS)
            frames = sorted(set(list(range(0, length + 1, spacing)) + [length]))
            previous = {}
            floor_corrections = []
            for frame in frames:
                scene.frame_set(frame + 1)
                function(frame / length)
                floor_corrections.append(ground_correct())
                for bone in arm.pose.bones:
                    if bone.name in previous:
                        bone.rotation_quaternion.make_compatible(previous[bone.name])
                    previous[bone.name] = bone.rotation_quaternion.copy()
                    bone.keyframe_insert(data_path='location', frame=frame + 1, group=bone.name)
                    bone.keyframe_insert(data_path='rotation_quaternion', frame=frame + 1, group=bone.name)
                    bone.keyframe_insert(data_path='scale', frame=frame + 1, group=bone.name)
            slot = arm.animation_data.action_slot
            for layer in action.layers:
                for strip in layer.strips:
                    bag = strip.channelbag(slot)
                    for channel in bag.fcurves:
                        for key in channel.keyframe_points:
                            key.interpolation = 'LINEAR'
            manifest.append({'name': name, 'duration_seconds': duration, 'frames': [1, length + 1],
                             'keys_per_channel': len(frames), 'in_place': name != 'death',
                             'max_floor_correction_m': max(floor_corrections),
                             'native_reference': '../source_audit/' + ('standing_native.png' if name == 'standing' else name + '_native.png')})
            return .2
        except Exception:
            status.write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
            return None

    bpy.app.timers.register(step, first_interval=.2)
    print('Scheduled', len(queue), 'native actions')


def activate(name, frame=1):
    arm = pose.rig()
    action = bpy.data.actions[name]
    arm.animation_data.action = action
    arm.animation_data.action_slot = action.slots[0]
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = round(action['duration_seconds'] * FPS) + 1
    bpy.context.scene.frame_set(frame)
