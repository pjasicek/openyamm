"""Inspect attack elbow bending and the exact frames reported by the user."""
import json
import math
import traceback

import bpy
from mathutils import Vector, Quaternion

import gallery
import motion
import pose
from mesh_tools import ROOT

OUTPUT = ROOT / 'review/attack_elbow_correction'


def observe(arm=None):
    arm = arm or pose.rig()
    result = {}
    for suffix in ['.R', '.L']:
        upper, lower = [arm.pose.bones[name + suffix] for name in ['upper_arm', 'forearm']]
        hand = arm.pose.bones['hand' + suffix]
        rest_upper = (lower.bone.head_local - upper.bone.head_local).normalized()
        rest_lower = (hand.bone.head_local - lower.bone.head_local).normalized()
        rest_axis = rest_upper.cross(rest_lower).normalized()
        delta = upper.matrix.to_quaternion() @ upper.bone.matrix_local.to_quaternion().inverted()
        axis = delta @ rest_axis
        u = (lower.head - upper.head).normalized()
        f = (hand.head - lower.head).normalized()
        result[suffix] = {
            'shoulder': list(upper.head), 'elbow': list(lower.head), 'wrist': list(lower.tail),
            'hinge_off_plane_degrees': math.degrees(math.asin(max(-1, min(1, axis.dot(f))))),
            'signed_flexion_degrees': math.degrees(math.atan2(axis.dot(u.cross(f)), u.dot(f))),
            'joint_gap_m': (upper.tail - lower.head).length,
            'wrist_bend_degrees': math.degrees(lower.vector.angle(arm.pose.bones['hand' + suffix].vector)),
            'upper_rotation': list(upper.matrix.to_quaternion()),
            'lower_rotation': list(lower.matrix.to_quaternion()),
        }
    return result


def measure(label, direct=False, samples=145, imported=False):
    import roundtrip
    assert not (direct and imported)
    scene = bpy.data.scenes['GB15 Export validation' if imported else 'MM6 Goblin - Authored 15K']
    bpy.context.window.scene = scene
    arm = next(obj for obj in scene.objects if obj.type == 'ARMATURE') if imported else pose.rig()
    records = []
    if direct:
        pose.rig().animation_data.action = None
    for index in range(samples):
        phase = index / (samples - 1)
        if direct:
            motion.attack(phase)
            motion.ground_correct()
        else:
            frame = 1 + phase * 36
            if imported:
                roundtrip.activate_import('attack', int(frame))
            else:
                motion.activate('attack', int(frame))
            bpy.context.scene.frame_set(int(frame), subframe=frame % 1)
        records.append({'phase': phase, 'arms': observe(arm)})
    summary = {}
    for suffix in ['.R', '.L']:
        arms = [record['arms'][suffix] for record in records]
        summary[suffix] = {
            'maximum_hinge_off_plane_degrees': max(abs(arm['hinge_off_plane_degrees']) for arm in arms),
            'minimum_signed_flexion_degrees': min(arm['signed_flexion_degrees'] for arm in arms),
            'maximum_wrist_bend_degrees': max(arm['wrist_bend_degrees'] for arm in arms),
            'maximum_joint_gap_m': max(arm['joint_gap_m'] for arm in arms),
            'maximum_elbow_step_m': max((Vector(a['elbow']) - Vector(b['elbow'])).length
                                         for a, b in zip(arms, arms[1:])),
            'maximum_upper_rotation_step_degrees': max(math.degrees(2 * math.acos(min(1, abs(
                Quaternion(a['upper_rotation']).dot(Quaternion(b['upper_rotation']))))))
                for a, b in zip(arms, arms[1:])),
        }
    report = {'sample_fps': (samples - 1) / .75, 'samples': records, 'summary': summary}
    (OUTPUT / (label + '_measurements.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(label, summary)
    return report


def preview(label):
    scene = bpy.data.scenes['MM6 Goblin - Authored 15K']
    bpy.context.window.scene = scene
    pose.rig().animation_data.action = None
    output = OUTPUT / label
    output.mkdir(parents=True, exist_ok=True)
    indices = [0, 3, 6, 7, 8, 9, 12, 15, 16, 17]
    tasks = [(index, view) for view in [0, 2, 6] for index in indices]
    manifest = json.loads((ROOT / 'review/complete_gallery/manifest.json').read_text())
    camera = manifest['cameras']['attack']
    scene.render.resolution_x = scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'

    def step():
        try:
            if not tasks:
                (output / 'status.json').write_text('{"state":"complete"}\n')
                return None
            index, view = tasks.pop(0)
            motion.attack(index / 18)
            motion.ground_correct()
            offset, rotation, _ = gallery.camera_basis(view, camera['elevation'])
            scene.camera.location = Vector(camera['target']) + offset
            scene.camera.rotation_euler = rotation.to_euler()
            scene.camera.data.ortho_scale = camera['scale']
            scene.render.filepath = str(output / (manifest['views'][view]['id'] + '_' + str(index).zfill(3) + '.png'))
            (output / 'status.json').write_text(json.dumps({'state': 'rendering', 'remaining': len(tasks)}))
            bpy.ops.render.render(write_still=True)
            return .03
        except Exception:
            (output / 'status.json').write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
            return None
    bpy.app.timers.register(step, first_interval=.2)
    print('Scheduled', len(tasks), label, 'previews')
