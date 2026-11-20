"""Focused attack-pose rendering and measured arm review for screenshot 2128."""
import json
import hashlib
import math
import traceback

import bpy
from mathutils import Vector, Quaternion

import motion
import pose
from mesh_tools import ROOT

OUTPUT = ROOT / 'review/attack_arm_correction'


def joints():
    arm = pose.rig()
    result = {}
    for suffix in ['.R', '.L']:
        upper, forearm, hand = [arm.pose.bones[name + suffix] for name in ['upper_arm', 'forearm', 'hand']]
        result[suffix] = {
            'shoulder': list(upper.head), 'elbow': list(upper.tail), 'wrist': list(hand.head),
            'elbow_flexion_degrees': math.degrees(upper.vector.angle(forearm.vector)),
            'wrist_bend_degrees': math.degrees(forearm.vector.angle(hand.vector)),
        }
    return result


def preview(label):
    scene = bpy.data.scenes['MM6 Goblin - Authored 15K']
    bpy.context.window.scene = scene
    pose.rig().animation_data.action = None
    output = OUTPUT / label
    output.mkdir(parents=True, exist_ok=True)
    tasks = [('front', index) for index in range(6)]
    tasks += [(view, index) for view in ['right', 'left', 'back'] for index in [0, 1, 2, 3, 4]]
    offsets = {'front': (0, -4, 0), 'right': (-4, 0, 0), 'left': (4, 0, 0), 'back': (0, 4, 0)}
    records = []

    def step():
        try:
            if not tasks:
                (output / 'joints.json').write_text(json.dumps(records, indent=2) + '\n')
                (output / 'status.json').write_text(json.dumps({'state': 'complete'}))
                return None
            view, index = tasks.pop(0)
            motion.attack(index / 6)
            motion.ground_correct()
            if view == 'front':
                records.append({'phase': 'ABCDEF'[index], 'time': index * .125, 'arms': joints()})
            offset = Vector(offsets[view])
            scene.camera.location = Vector((0, -.1, 1.00)) + offset
            scene.camera.rotation_euler = (-offset).to_track_quat('-Z', 'Y').to_euler()
            scene.camera.data.ortho_scale = 2.36
            bpy.data.objects['GB15 Ground'].hide_render = False
            scene.render.resolution_x = scene.render.resolution_y = 800
            scene.render.resolution_percentage = 100
            scene.render.image_settings.file_format = 'PNG'
            scene.render.filepath = str(output / (view + '_' + 'ABCDEF'[index] + '.png'))
            (output / 'status.json').write_text(json.dumps({'state': 'rendering', 'view': view, 'phase': index}))
            bpy.ops.render.render(write_still=True)
            return .05
        except Exception:
            (output / 'status.json').write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
            return None
    bpy.app.timers.register(step, first_interval=.2)
    print('Scheduled', len(tasks), 'attack pose previews:', label)


def measure(output=None, action_name='attack'):
    """Inspect the actual baked action, including quarter-frame interpolation."""
    import motion_review
    records = []
    for index in range(145):
        frame = 1 + index * .25
        integer = int(frame)
        motion.activate(action_name, integer)
        bpy.context.scene.frame_set(integer, subframe=frame - integer)
        record = motion_review.observe((frame - 1) / 48)
        record['arms_anatomy'] = joints()
        record['rotations'] = {name: list(pose.rig().pose.bones[name].matrix.to_quaternion())
                               for name in ['upper_arm.R', 'forearm.R', 'hand.R',
                                            'upper_arm.L', 'forearm.L', 'hand.L']}
        record['all_joints'] = {bone.name: list(bone.head) for bone in pose.rig().pose.bones}
        record['maximum_bone_scale_error'] = max(abs(value - 1) for bone in pose.rig().pose.bones
                                                  for value in bone.matrix.to_scale())
        records.append(record)
    steps = {}
    for name in records[0]['rotations']:
        angles = [math.degrees(2 * math.acos(min(1, abs(Quaternion(a['rotations'][name]).dot(
                  Quaternion(b['rotations'][name])))))) for a, b in zip(records, records[1:])]
        steps[name] = max(angles)
    dots = []
    for index, record in enumerate(records[1:-1], 1):
        if .44 <= record['time'] / .75 <= .67:
            velocity = Vector(records[index + 1]['blade_center']) - Vector(records[index - 1]['blade_center'])
            axis = Vector(record['blade_axis'])
            transverse = (velocity - axis * velocity.dot(axis)).normalized()
            dots.append({'phase': record['time'] / .75, 'edge_dot_transverse_travel':
                         Vector(record['blade_edge']).dot(transverse)})
    report = {
        'sample_count': len(records), 'sample_fps': 192,
        'maximum_bone_scale_error': max(r['maximum_bone_scale_error'] for r in records),
        'max_quarter_frame_rotation_degrees': steps,
        'maximum_wrist_bend_degrees': {suffix: max(r['arms_anatomy'][suffix]['wrist_bend_degrees']
                                      for r in records) for suffix in ['.R', '.L']},
        'loop_joint_error_m': max((Vector(records[0]['all_joints'][name]) -
                                  Vector(records[-1]['all_joints'][name])).length
                                 for name in records[0]['all_joints']),
        'cutting_edge_samples': dots, 'samples': records,
    }
    (output or OUTPUT / 'measurements.json').write_text(json.dumps(report, indent=2) + '\n')
    print({key: value for key, value in report.items() if key not in ['samples', 'cutting_edge_samples']})
    print('Cutting edge:', [(round(r['phase'], 3), round(r['edge_dot_transverse_travel'], 3)) for r in dots])
    return report


def refresh_gallery(revision='attack_arm_7'):
    """Replace the attack views after proving the other six actions and all surfaces identical."""
    import numpy as np
    import gallery
    import roundtrip
    output = ROOT / 'review/complete_gallery'
    validation = json.loads((ROOT / 'delivery/textured_validation.json').read_text())
    assert validation['status'] == 'pass' and validation['only_changed_animation'] == 'attack'
    assert validation['all_bind_surfaces_topology_uvs_normals_weights_identical']
    assert validation['all_materials_and_packed_images_identical']
    manifest = json.loads((output / 'manifest.json').read_text())
    assert manifest['source_sha256'] == validation['baseline_sha256'], 'Gallery is not the measured baseline.'
    roundtrip.import_latest(gallery.SOURCE, ROOT / 'delivery/textured_roundtrip_validation.json')
    scene = bpy.data.scenes['GB15 Export validation']
    scene.render.resolution_x = scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.compression = 30
    scene.eevee.taa_render_samples = 64
    bpy.data.objects['GB15 Ground'].hide_render = False
    camera = manifest['cameras']['attack']
    points = []
    for frame in range(1, 38):
        roundtrip.activate_import('attack', frame)
        graph = bpy.context.evaluated_depsgraph_get()
        for obj in scene.objects:
            if obj.type == 'MESH' and obj.name != 'GB15 Ground':
                evaluated = obj.evaluated_get(graph)
                points.extend(evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box)
    points = np.asarray(points) - np.asarray(camera['target'])
    bounds = {}
    for index, view in enumerate(manifest['views']):
        basis = gallery.camera_basis(index, camera['elevation'])[2]
        projected = points @ basis.T
        margin = float((.5 - np.abs(projected[:, :2]) / camera['scale']).min())
        # Keep the existing comparison cameras; even conservative mesh boxes retain 29 px at 960 px.
        assert margin >= .03, (view['id'], margin)
        bounds[view['id']] = {'minimum_frame_margin': margin}
    new_hash = hashlib.sha256(gallery.SOURCE.read_bytes()).hexdigest()
    assert new_hash == validation['source_sha256']
    for clip in manifest['clips']:
        if clip['action'] == 'attack':
            clip['folder'] = 'frames/' + revision + '/' + clip['view']
            clip['poster'] = clip['folder'] + '/000.png'
            clip['video'] = 'videos/' + revision + '__' + clip['view'] + '.mp4'
            clip['render_source_sha256'] = new_hash
            (output / clip['folder']).mkdir(parents=True, exist_ok=True)
        else:
            clip.setdefault('render_source_sha256', manifest['source_sha256'])
            clip['identical_current_data_verified_by'] = '../../delivery/textured_validation.json'
    manifest['revision'] = revision
    manifest['source_sha256'] = new_hash
    manifest['framing']['attack'] = bounds
    manifest['attack_review'] = '../attack_arm_correction/index.html'
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'gallery-data.js').write_text('window.GOBLIN_GALLERY = ' + json.dumps(manifest) + ';\n')
    framing = json.loads((output / 'framing_validation.json').read_text())
    framing['source_sha256'] = new_hash
    framing['clip_margins']['attack'] = bounds
    framing['attack_revision'] = '37 exported poses in eight unchanged cameras; other six actions are identical.'
    (output / 'framing_validation.json').write_text(json.dumps(framing, indent=2) + '\n')
    (output / 'roundtrip_validation.json').write_bytes((ROOT / 'delivery/textured_roundtrip_validation.json').read_bytes())
    print('Prepared eight revised attack videos in the existing comparison cameras. Other clips remain identical.')
