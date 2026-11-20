"""Inspect whole-body walking motion in world coordinates, with before/after receipts."""
import json
import math

import bpy
from mathutils import Vector

import motion
import pose
from mesh_tools import ROOT

FOLDER = ROOT / 'review/body_motion_correction'


def observe(arm, frame):
    world = arm.matrix_world
    result = {'frame': frame, 'bones': {}, 'shoulders': {}}
    for name in ['pelvis', 'spine', 'chest', 'head', 'thigh.L', 'thigh.R', 'foot.L', 'foot.R',
                 'upper_arm.L', 'upper_arm.R']:
        bone = arm.pose.bones[name]
        delta = world @ bone.matrix @ bone.bone.matrix_local.inverted() @ world.inverted()
        forward = delta.to_3x3() @ Vector((0, -1, 0))
        result['bones'][name] = {'head': list(world @ bone.head), 'tail': list(world @ bone.tail),
                                 'yaw': math.degrees(math.atan2(forward.x, -forward.y))}
    chest = arm.pose.bones['chest'].matrix.to_quaternion()
    for suffix in ['.L', '.R']:
        upper = arm.pose.bones['upper_arm' + suffix]
        cap = arm.pose.bones['pauldron' + suffix]
        result['shoulders'][suffix] = list(chest.inverted() @ (cap.head - upper.head))
    return result


def describe(rows):
    def span(name, key):
        values = [row['bones'][name][key] for row in rows]
        return [min(values), max(values)]
    lean = []
    for row in rows:
        bones = row['bones']
        # glTF stores joint origins, not Blender display-bone tail lengths.
        direction = Vector(bones['head']['head']) - Vector(bones['pelvis']['head'])
        lean.append(math.degrees(math.atan2(-direction.y, direction.z)))
    contact_separation = [abs(rows[i]['bones']['foot.L']['head'][1] - rows[i]['bones']['foot.R']['head'][1])
                          for i in [0, 24]]
    height = [row['bones']['pelvis']['head'][2] for row in rows]
    result = {'yaw_ranges_degrees': {name: span(name, 'yaw') for name in ['pelvis', 'chest', 'head']},
              'torso_forward_lean_degrees': [min(lean), max(lean)],
              'contact_ankle_fore_aft_separation_m': contact_separation,
              'pelvis_height_range_m': [min(height), max(height)]}
    if 'shoulders' in rows[0]:
        result['shoulder_attachment_max_step_m'] = {
            suffix: max((Vector(a['shoulders'][suffix]) - Vector(b['shoulders'][suffix])).length
                        for a, b in zip(rows, rows[1:])) for suffix in ['.L', '.R']}
    return result


def audit(imported=False):
    if imported:
        import roundtrip
        arm = roundtrip.activate_import('walk', 1)
    else:
        bpy.context.window.scene = bpy.data.scenes['MM6 Goblin - Authored 15K']
        motion.activate('walk')
        arm = pose.rig()
    scene = bpy.context.scene
    rows = []
    for frame in range(1, 50):
        scene.frame_set(frame)
        rows.append(observe(arm, frame))
    after = describe(rows)
    before = describe(json.loads((FOLDER / 'before_measurements.json').read_text()))
    yaw = after['yaw_ranges_degrees']
    assert yaw['chest'][0] < -30 and yaw['chest'][1] > 30
    assert 8 < max(abs(v) for v in yaw['pelvis']) < 15
    assert max(abs(v) for v in yaw['head']) < 20
    assert min(after['contact_ankle_fore_aft_separation_m']) > .50
    assert 8 < min(after['torso_forward_lean_degrees']) < 18
    assert max(after['torso_forward_lean_degrees']) < 18
    assert all(v < .002 for v in after['shoulder_attachment_max_step_m'].values())
    # The source b/e body turn, stepping leg and opposite arm are now aligned at contacts.
    for index, leading in [(0, '.R'), (24, '.L')]:
        other = '.L' if leading == '.R' else '.R'
        bones = rows[index]['bones']
        assert bones['foot' + leading]['head'][1] < bones['foot' + other]['head'][1]
        assert bones['upper_arm' + other]['tail'][1] < bones['upper_arm' + leading]['tail'][1]
    assert rows[0]['bones']['chest']['yaw'] < -30 and rows[24]['bones']['chest']['yaw'] > 30
    assert rows[0]['bones']['pelvis']['yaw'] > 8 and rows[24]['bones']['pelvis']['yaw'] < -8
    assert rows[12]['bones']['pelvis']['head'][2] > rows[0]['bones']['pelvis']['head'][2] + .025
    assert rows[36]['bones']['pelvis']['head'][2] > rows[24]['bones']['pelvis']['head'][2] + .025
    closure = max((Vector(rows[0]['bones'][name]['head']) - Vector(rows[-1]['bones'][name]['head'])).length
                  for name in rows[0]['bones'])
    assert closure < .00001
    report = {'status': 'pass', 'source': 'reimported GLB' if imported else 'authored Blender walk',
              'frames': 49, 'sample_fps': 48, 'before': before, 'after': after,
              'measured_joint_loop_error_m': closure,
              'references': ['test_img/2117.png', 'test_img/2118.png',
                             'mm6_goblin/direct_complete/native/gobwab2.png',
                             'mm6_goblin/direct_complete/native/gobwae2.png'],
              'interpretation': 'Chest/back alternation, hip opposition and longer stride from native silhouettes; '
                                'angles are authored estimates, not recovered source transforms.'}
    (FOLDER / ('export_measurements.json' if imported else 'after_measurements.json')).write_text(
        json.dumps(rows, indent=2) + '\n')
    (ROOT / 'delivery' / ('body_export_validation.json' if imported else 'body_validation.json')).write_text(
        json.dumps(report, indent=2) + '\n')
    if imported:
        roundtrip.activate_import('standing', 1)
    else:
        motion.activate('standing')
    print(json.dumps(report, indent=2))
    return report
