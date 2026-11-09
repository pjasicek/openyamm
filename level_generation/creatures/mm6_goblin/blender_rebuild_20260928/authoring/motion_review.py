"""Observe real posed joints, cutting-edge travel and shoulder clearance; render focused poses."""
import json
import math
import traceback

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import motion
import pose
from mesh_tools import ROOT


def observe(time, clearance=False):
    arm = pose.rig()
    chest = arm.pose.bones['chest']
    q = chest.matrix.to_quaternion().inverted()
    record = {'time': time, 'arms': {}}
    tree = (BVHTree.FromObject(bpy.data.objects['GB15 Skin body'], bpy.context.evaluated_depsgraph_get())
            if clearance else None)
    for suffix in ['.R', '.L']:
        upper = arm.pose.bones['upper_arm' + suffix]
        plate = arm.pose.bones['pauldron' + suffix]
        data = {'upper_direction': list(q @ upper.vector.normalized()), 'elbow': list(upper.tail),
                'wrist': list(arm.pose.bones['hand' + suffix].head),
                'plate_relative_position': list(q @ (plate.head - upper.head)),
                'plate_relative_rotation': list(q @ plate.matrix.to_quaternion()),
                'foot': list(arm.pose.bones['foot' + suffix].head)}
        if tree:
            obj = bpy.data.objects['GB15 Shoulder' + suffix]
            transform = plate.matrix @ plate.bone.matrix_local.inverted()
            distances = []
            for vertex in obj.data.vertices[:65]:
                point = transform @ vertex.co
                hit, normal, face, distance = tree.find_nearest(point)
                distances.append((point - hit).dot(normal))
            data['minimum_shell_skin_clearance_m'] = min(distances)
        record['arms'][suffix] = data
    weapon = arm.pose.bones['weapon.R']
    deform = weapon.matrix @ weapon.bone.matrix_local.inverted()
    info = pose.WEAPON
    record['blade_center'] = list(deform @ (Vector(info['center']) + Vector(info['axis']) * .43))
    record['blade_edge'] = list((deform.to_3x3() @ Vector(info['broad'])).normalized())
    record['blade_axis'] = list(weapon.vector.normalized())
    head_delta = arm.pose.bones['head'].matrix.to_quaternion() @ arm.data.bones['head'].matrix_local.to_quaternion().inverted()
    record['head_forward'] = list(head_delta @ Vector((0, -1, 0)))
    return record


def summary(records):
    result = {}
    for name, samples in records.items():
        stats = {}
        for suffix in ['.R', '.L']:
            arms = [sample['arms'][suffix] for sample in samples]
            directions = [Vector(arm['upper_direction']) for arm in arms]
            angle = max(a.angle(b) for a in directions for b in directions)
            offsets = [Vector(arm['plate_relative_position']) for arm in arms]
            step = max((a - b).length for a, b in zip(offsets, offsets[1:]))
            stats[suffix] = {'upper_arm_excursion_degrees': math.degrees(angle),
                             'max_plate_relative_step_m': step}
            if 'plate_relative_rotation' in arms[0]:
                from mathutils import Quaternion
                rotations = [Quaternion(arm['plate_relative_rotation']) for arm in arms]
                stats[suffix]['max_plate_relative_rotation_step_degrees'] = max(
                    math.degrees(2 * math.acos(min(1, abs(a.dot(b)))))
                    for a, b in zip(rotations, rotations[1:]))
            if 'minimum_shell_skin_clearance_m' in arms[0]:
                stats[suffix]['minimum_shell_skin_clearance_m'] = min(
                    arm['minimum_shell_skin_clearance_m'] for arm in arms)
        if name == 'attack':
            dots = []
            for i in range(1, len(samples) - 1):
                sample = samples[i]
                if .39 <= sample['time'] / .75 <= .69:
                    velocity = Vector(samples[i + 1]['blade_center']) - Vector(samples[i - 1]['blade_center'])
                    axis = Vector(sample['blade_axis'])
                    transverse = (velocity - axis * velocity.dot(axis)).normalized()
                    dots.append(Vector(sample['blade_edge']).dot(transverse))
            stats['minimum_cut_edge_dot_transverse_travel'] = min(dots)
            if 'head_forward' in samples[0]:
                stats['preparation_head_pitch_degrees'] = max(
                    math.degrees(math.asin(max(-1, min(1, sample['head_forward'][2]))))
                    for sample in samples if .15 <= sample['time'] / .75 <= .35)
        result[name] = stats
    return result


def validate():
    """Regress the reported motion faults using actual sampled joint and weapon transforms."""
    output = ROOT / 'review/motion_correction'
    before = summary(json.loads((output / 'before/measurements.json').read_text()))
    measured = json.loads((output / 'after/measurements.json').read_text())
    after, records = measured['summary'], measured['clips']
    walk = {}
    for suffix in ['.R', '.L']:
        old, new = before['walk'][suffix], after['walk'][suffix]
        assert new['upper_arm_excursion_degrees'] > 40, new
        assert new['max_plate_relative_step_m'] < .002, new
        assert new['max_plate_relative_step_m'] < old['max_plate_relative_step_m'] * .25, (old, new)
        walk[suffix] = {'before': old, 'after': {key: new[key] for key in
                        ['upper_arm_excursion_degrees', 'max_plate_relative_step_m',
                         'max_plate_relative_rotation_step_degrees']}}
    # Measure opposition along the direction with the largest arm-swing variance.
    arms = [[Vector(sample['arms'][suffix]['upper_direction']) for sample in records['walk']]
            for suffix in ['.R', '.L']]
    means = [sum(values, Vector()) / len(values) for values in arms]
    centered = [[value - mean for value in values] for values, mean in zip(arms, means)]
    axis = max(range(3), key=lambda i: sum(value[i]**2 for values in centered for value in values))
    a, b = [[value[axis] for value in values] for values in centered]
    correlation = sum(x*y for x, y in zip(a, b)) / math.sqrt(sum(x*x for x in a) * sum(y*y for y in b))
    assert correlation < -.99, correlation
    attack = after['attack']
    assert attack['minimum_cut_edge_dot_transverse_travel'] > .97, attack
    assert 12 < attack['preparation_head_pitch_degrees'] < 35, attack
    prepare = [sample for sample in records['attack'] if .15 <= sample['time'] / .75 <= .35]
    head_turn = max(abs(math.degrees(math.atan2(sample['head_forward'][0], -sample['head_forward'][1])))
                    for sample in prepare)
    assert head_turn > 8, head_turn
    loop_errors = {}
    for name, samples in records.items():
        if name == 'death':
            continue
        first, last = samples[0], samples[-1]
        errors = [(Vector(first[key]) - Vector(last[key])).length
                  for key in ['blade_center', 'blade_edge', 'blade_axis', 'head_forward']]
        for suffix in ['.R', '.L']:
            errors += [(Vector(first['arms'][suffix][key]) - Vector(last['arms'][suffix][key])).length
                       for key in ['elbow', 'wrist', 'foot', 'plate_relative_position']]
        loop_errors[name] = max(errors)
        assert max(errors) < .00001, (name, max(errors))
    report = {'status': 'pass', 'sample_fps': 48, 'samples': sum(map(len, records.values())),
              'walk_seconds': 1, 'walk': walk, 'walk_arm_swing_correlation': correlation,
              'attack_cut_edge_dot_transverse_travel': attack['minimum_cut_edge_dot_transverse_travel'],
              'attack_preparation_head_pitch_degrees': attack['preparation_head_pitch_degrees'],
              'attack_preparation_head_turn_degrees': head_turn, 'loop_endpoint_max_errors': loop_errors,
              'scope': ('Baked authored poses: walking upper-arm excursion/opposition and cap continuity, '
                        'cutting edge travel, preparation head lift/turn and loop closure. '
                        'Nearest-face signed distances in the diagnostic measurements are not a closed-volume '
                        'collision test; visual review is also required.')}
    (ROOT / 'delivery/motion_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Motion validation passed;', report['samples'], 'sampled frames')
    return report


def audit(label='v1', baked=False):
    output = ROOT / 'review/motion_correction' / label
    output.mkdir(parents=True, exist_ok=True)
    records = {}
    queue = list(motion.CLIPS)
    arm = pose.rig()
    if not baked:
        arm.animation_data.action = None

    def step():
        try:
            if not queue:
                report = {'clips': records, 'summary': summary(records)}
                (output / 'measurements.json').write_text(json.dumps(report, indent=2) + '\n')
                (output / 'audit_status.json').write_text(json.dumps({'state': 'complete'}))
                return None
            name, duration, spacing, function = queue.pop(0)
            (output / 'audit_status.json').write_text(json.dumps({'state': 'measuring', 'clip': name}))
            samples = []
            for frame in range(0, round(duration * 48) + 1, 1 if baked else 3):
                if baked:
                    motion.activate(name, frame + 1)
                else:
                    function(frame / (duration * 48))
                    motion.ground_correct()
                record = observe(frame / 48, clearance=True)
                record['frame'] = frame + 1
                samples.append(record)
            records[name] = samples
            return .1
        except Exception:
            (output / 'audit_status.json').write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
            return None

    bpy.app.timers.register(step, first_interval=.2)
    print('Scheduled', label, 'motion audit')


def render(label='v1'):
    output = ROOT / 'review/motion_correction' / label
    output.mkdir(parents=True, exist_ok=True)
    scene = bpy.data.scenes['MM6 Goblin - Authored 15K']
    bpy.context.window.scene = scene
    pose.rig().animation_data.action = None
    tasks = [('attack_' + str(i), 'attack', t, 'front')
             for i, t in enumerate([0, .18, .32, .46, .55, .68, .85])]
    tasks += [('walk_' + str(i), 'walk', t, 'quarter') for i, t in enumerate([0, .25, .5, .75])]
    tasks += [('walk_side_' + str(i), 'walk', t, 'side') for i, t in enumerate([0, .5])]
    tasks += [('attack_head', 'attack', .23, 'head'), ('attack_quarter', 'attack', .46, 'quarter'),
              ('hit', 'hit', .28, 'quarter'), ('death', 'death', 1, 'corpse')]

    def step():
        try:
            if not tasks:
                pose.standing()
                (output / 'render_status.json').write_text(json.dumps({'state': 'complete'}))
                return None
            name, action, t, view = tasks.pop(0)
            (output / 'render_status.json').write_text(json.dumps({'state': 'rendering', 'name': name}))
            getattr(motion, action)(t)
            motion.ground_correct()
            target, offset, scale = Vector((0, -.10, 1.02)), Vector((0, -4, 0)), 2.35
            if view == 'quarter':
                offset = Vector((-3, -5, 1.3))
            if view == 'side':
                offset = Vector((-4, 0, 0))
            if view == 'head':
                target, offset, scale = Vector((0, 0, 1.57)), Vector((0, -4, 0)), .48
            if view == 'corpse':
                target, offset, scale = Vector((0, -.65, .19)), Vector((-2.3, -2.85, 3.01)), 2.1
            bpy.data.objects['GB15 Ground'].hide_render = view == 'head'
            scene.camera.location = target + offset
            scene.camera.rotation_euler = (-offset).to_track_quat('-Z', 'Y').to_euler()
            scene.camera.data.ortho_scale = scale
            scene.render.resolution_x = 900
            scene.render.resolution_y = 1000 if view != 'head' else 900
            scene.render.filepath = str(output / (name + '.png'))
            bpy.ops.render.render(write_still=True)
            return .1
        except Exception:
            (output / 'render_status.json').write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
            return None

    bpy.app.timers.register(step, first_interval=.2)
    print('Scheduled', label, len(tasks), 'motion pose renders')
